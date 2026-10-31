extends Control
## Results: the outcome, what the sequences earned, timing feedback, unlocks, and Next mission / Retry / Change choices
## / Menu. Chart ids and diagnostics stay out of it (F3 debug in play shows them). The legacy duel keeps its summary.


func _ready() -> void:
	var r := Session.last_result
	var outcome := str(r.get("outcome", "incomplete"))
	var head: String = {"victory": "VICTORY", "defeat": "DEFEAT", "complete": "PRACTICE COMPLETE" if bool(r.get("practice", false)) else "SONG COMPLETE"}.get(outcome, "SONG OVER")
	var parts := UiStyle.screen(self, "%s   %s" % [head, str(r.get("level", ""))])
	var content: VBoxContainer = parts["content"]
	if str(r.get("mode", "")) == "mission":
		_mission(content, r)
	else:
		_duel(content, r)
	var buttons := HFlowContainer.new()
	buttons.add_theme_constant_override("h_separation", UiStyle.GAP)
	buttons.add_theme_constant_override("v_separation", UiStyle.GAP)
	content.add_child(buttons)
	var first: Button = null
	var camp: Dictionary = r.get("campaign", {})
	var next_n := int(camp.get("unlocked_level", 0))
	if next_n == 0 and str(r.get("mode", "")) == "mission" and outcome == "victory":
		next_n = Session.mission_number + 1
	if next_n > 0 and Session.campaign.is_playable(next_n) and Session.campaign.is_unlocked(next_n) and not bool(r.get("practice", false)):
		first = UiStyle.button("Next mission", func() -> void:
			Session.mission_number = next_n
			get_tree().change_scene_to_file("res://src/scenes/mission_setup.tscn"), 240, 64)
		buttons.add_child(first)
	var retry := UiStyle.button("Retry", func() -> void: get_tree().change_scene_to_file("res://src/scenes/play.tscn"), 200, 64)
	buttons.add_child(retry)
	if str(r.get("mode", "")) == "mission":
		buttons.add_child(UiStyle.button("Change choices", func() -> void: get_tree().change_scene_to_file("res://src/scenes/mission_setup.tscn"), 240, 64))
	buttons.add_child(UiStyle.button("Menu", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"), 160, 64))
	(first if first != null else retry).grab_focus()


func _mission(content: VBoxContainer, r: Dictionary) -> void:
	var outcome := str(r.get("outcome", ""))
	var lines: Array[String] = []
	var seqs := int(r.get("sequences", 0))
	lines.append("Sequences completed: %d of %d" % [int(r.get("sequences_passed", 0)), seqs])
	var mean := float(r.get("mean_ms", 0.0))
	var tendency := "on the beat" if absf(mean) < 12.0 else ("a little late" if mean > 0.0 else "a little early")
	lines.append("Timing: %.0f ms from the beat on average, %s" % [float(r.get("mean_abs_ms", 0.0)), tendency])
	var g: Dictionary = r.get("grades", {})
	lines.append("Build speed: sharp %d   steady %d   loose %d" % [int(g.get("sharp", 0)), int(g.get("steady", 0)), int(g.get("loose", 0))])
	var holds := int(r.get("holds_complete", 0)) + int(r.get("holds_partial", 0))
	if holds > 0:
		lines.append("Holds kept to the end: %d of %d" % [int(r.get("holds_complete", 0)), holds])
	if bool(r.get("battle", true)):
		lines.append("Earned: %d defenses, %d units, %d repairs" % [int(r.get("built", 0)), int(r.get("units", 0)), int(r.get("repairs", 0))])
		var hp: Dictionary = r.get("objective_hp", {}).get("command_core", {"hp": 0, "max": 1})
		if outcome == "victory":
			lines.append("The command core held at %d%%." % int(round(100.0 * float(hp["hp"]) / maxf(float(hp["max"]), 1.0))))
		elif outcome == "defeat":
			lines.append("Lost the %s." % str(r.get("reason", "")).replace("objective_destroyed:", "").replace("_", " "))
	for line in lines:
		content.add_child(UiStyle.note(line, UiStyle.TEXT, 22))
	var camp: Dictionary = r.get("campaign", {})
	if bool(r.get("practice", false)):
		content.add_child(UiStyle.note("Practice: nothing was saved.", UiStyle.MUTED))
	elif not camp.is_empty():
		if camp.get("first_clear", false):
			content.add_child(UiStyle.note("Mission cleared.", UiStyle.GOOD, 24))
			if int(camp.get("unlocked_level", 0)) > 0:
				content.add_child(UiStyle.note("Unlocked: %s" % str(camp.get("unlocked_title", "")), UiStyle.GOOD, 22))
			var names: Array[String] = []
			for id in camp.get("new_options", []):
				names.append(_name(str(id)))
			if not names.is_empty():
				content.add_child(UiStyle.note("New choices: " + ", ".join(PackedStringArray(names)), UiStyle.GOOD, 20))
		if not camp.get("saved", true):
			content.add_child(UiStyle.note("Progress could not be saved.", UiStyle.WARN))
	elif outcome == "defeat":
		content.add_child(UiStyle.note("Missed sequences cost nothing but their reward. Defenses built early pay off.", UiStyle.MUTED))


## Friendly name of a library option (data/campaign/library_names.json, written by the content build).
func _name(id: String) -> String:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://data/campaign/library_names.json"))
	return str(parsed.get(id, id)) if typeof(parsed) == TYPE_DICTIONARY else id


func _duel(content: VBoxContainer, r: Dictionary) -> void:
	var rewards: Dictionary = r.get("rewards", {})
	content.add_child(UiStyle.note("Accuracy %.1f%%  (%d notes judged)\nPerfect %d   Good %d   Misses %d   Stray %d\nBest combo %d\nTanks %d   Infantry %d   Air actions %d" % [
		float(r.get("accuracy", 0.0)) * 100.0, int(r.get("judged", 0)),
		int(r.get("perfect", 0)), int(r.get("good", 0)), int(r.get("misses", 0)), int(r.get("strays", 0)),
		int(r.get("best_combo", 0)), int(rewards.get("kick", 0)), int(rewards.get("snare", 0)) * 5, int(rewards.get("bass", 0))], UiStyle.TEXT, 22))
