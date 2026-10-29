extends Control
## Result screen: outcome, accuracy, misses, best combo and battle duration. Retry resets everything.


func _ready() -> void:
	var r := Session.last_result
	var outcome := str(r.get("outcome", "incomplete"))
	$Box/Outcome.text = {"victory": "VICTORY", "defeat": "DEFEAT"}.get(outcome, "SONG COMPLETE")
	$Box/Title.text = str(r.get("level", ""))
	var rewards: Dictionary = r.get("rewards", {})
	if str(r.get("mode", "")) == "defense":
		_show_defense(r, rewards)
		return
	$Box/Stats.text = "Accuracy %.1f%%  (%d notes judged)\nPerfect %d   Good %d   Misses %d   Stray %d\nBest combo %d\nTanks %d   Infantry %d   Air actions %d\nDuration %d:%02d" % [
		float(r.get("accuracy", 0.0)) * 100.0, int(r.get("judged", 0)),
		int(r.get("perfect", 0)), int(r.get("good", 0)), int(r.get("misses", 0)), int(r.get("strays", 0)),
		int(r.get("best_combo", 0)),
		int(rewards.get("kick", 0)), int(rewards.get("snare", 0)) * 5, int(rewards.get("bass", 0)),
		int(r.get("duration_s", 0.0)) / 60, int(r.get("duration_s", 0.0)) % 60]
	$Box/Retry.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/play.tscn"))
	$Box/Menu.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	$Box/Retry.grab_focus()


func _show_defense(r: Dictionary, rewards: Dictionary) -> void:
	var lines: Array[String] = []
	lines.append("%s   chart %s" % [r.get("level", ""), r.get("chart_id", "")])
	lines.append("Accuracy %.1f%%  (%d notes judged)" % [float(r.get("accuracy", 0.0)) * 100.0, int(r.get("judged", 0))])
	lines.append("Perfect %d   Good %d   Misses %d   Stray %d   Best combo %d" % [int(r.get("perfect", 0)), int(r.get("good", 0)), int(r.get("misses", 0)), int(r.get("strays", 0)), int(r.get("best_combo", 0))])
	var per_slot: Array[String] = []
	for slot in rewards:
		per_slot.append("%s %d" % [slot, int(rewards[slot])])
	lines.append("Rewards: " + ", ".join(PackedStringArray(per_slot)))
	if not bool(r.get("battle", true)):
		lines.append("Rhythm-only playtest: no battle was played.")
	if str(r.get("outcome", "")) == "defeat":
		lines.append("Defeat: %s" % str(r.get("reason", "")).replace("objective_destroyed:", "lost the ").replace("_", " "))
	elif str(r.get("outcome", "")) == "victory":
		var hp: Dictionary = r.get("objective_hp", {}).get("command_core", {"hp": 0, "max": 1})
		lines.append("Survived to the end with the command core at %d%%." % int(round(100.0 * float(hp["hp"]) / maxf(float(hp["max"]), 1.0))))
	var camp: Dictionary = r.get("campaign", {})
	if bool(r.get("practice", false)):
		lines.append("Practice: nothing was saved.")
	elif not camp.is_empty():
		if camp.get("first_clear", false):
			lines.append("LEVEL CLEARED.")
			if int(camp.get("unlocked_level", 0)) > 0:
				lines.append("Level %d, %s, is unlocked." % [int(camp["unlocked_level"]), camp.get("unlocked_title", "")])
			var names: Array[String] = []
			for id in camp.get("new_profiles", []):
				names.append(Session.campaign.catalogue.display_name(str(id)))
			if not names.is_empty():
				lines.append("New instruments: " + ", ".join(PackedStringArray(names)))
		else:
			lines.append("Replay: your clears and unlocks are kept; bests only improve.")
		if not camp.get("saved", true):
			lines.append("Warning: progress could not be saved.")
	var next_n := int(camp.get("unlocked_level", 0))
	if next_n > 0 and Session.campaign.is_playable(next_n):
		var nb := Button.new()
		nb.text = "Next level"
		nb.custom_minimum_size = Vector2(0, 56)
		nb.add_theme_font_size_override("font_size", 24)
		nb.pressed.connect(func() -> void:
			Session.loadout_level_number = next_n
			get_tree().change_scene_to_file("res://src/scenes/loadout.tscn"))
		$Box.add_child(nb)
		$Box.move_child(nb, $Box/Retry.get_index())
	$Box/Stats.text = "
".join(PackedStringArray(lines))
	$Box/Retry.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/play.tscn"))
	$Box/Menu.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	$Box/Retry.grab_focus()
