extends Control
## The end-of-set summary: the ending reached, what the room did, the moments that went your way (or did not) and the energy over
## the set. Retry, back to the story menu, or home.

const NAMES := {"legendary_set": "LEGENDARY SET", "good_night": "GOOD NIGHT", "lost_the_floor": "LOST THE FLOOR"}


func _ready() -> void:
	var r := Session.story_result
	var ending := str(r.get("ending", "lost_the_floor"))
	var parts := UiStyle.screen(self, "Night One   %s" % str(NAMES.get(ending, "")))
	var content: VBoxContainer = parts["content"]
	var loaded := StoryData.load_file()
	var data: StoryData = loaded["data"]
	if data != null and data.endings.has(ending):
		content.add_child(UiStyle.note(str(data.endings[ending]["text"]), Color(0.9, 0.92, 1.0), 24))
	var lines := [
		"Sequences passed: %d of %d" % [int(r.get("sequences_passed", 0)), int(r.get("sequences_total", 0))],
		"Accuracy: %d%%     Best combo: %d" % [int(round(float(r.get("accuracy", 0.0)) * 100.0)), int(r.get("best_combo", 0))],
		"Crowd energy at close: %d     Peak: %d" % [int(float(r.get("energy", 0.0))), int(float(r.get("peak_energy", 0.0)))],
	]
	for l in lines:
		content.add_child(UiStyle.note(l, Color(0.85, 0.88, 0.95), 22))
	content.add_child(UiStyle.title("The night in moments", 24))
	for b in r.get("branches", []):
		var good := str(b["outcome"]) == "good"
		if str(b["text"]).is_empty():
			continue
		content.add_child(UiStyle.note("%s   (bar %d)\n%s" % [str(b["title"]), int(b["bar"]), str(b["text"])], UiStyle.GOOD if good else UiStyle.WARN, 18))
	var curve := EnergyCurve.new()
	curve.values = r.get("energy_curve", [])
	curve.custom_minimum_size = Vector2(0, 110)
	content.add_child(curve)
	var buttons := HFlowContainer.new()
	buttons.add_theme_constant_override("h_separation", UiStyle.GAP)
	content.add_child(buttons)
	var retry := UiStyle.button("Play again", func() -> void: get_tree().change_scene_to_file("res://src/scenes/story_play.tscn"), 220, 64)
	buttons.add_child(retry)
	buttons.add_child(UiStyle.button("Story Campaign", func() -> void: get_tree().change_scene_to_file("res://src/scenes/story_campaign.tscn"), 240, 64))
	buttons.add_child(UiStyle.button("Menu", func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"), 160, 64))
	retry.grab_focus()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/story_campaign.tscn")


## Crowd energy after each two-bar sequence.
class EnergyCurve:
	extends Control
	var values: Array = []

	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, size), Color(0.06, 0.07, 0.12))
		if values.size() < 2:
			return
		for mark in [30.0, 65.0, 85.0]:
			var y: float = size.y - size.y * float(mark) / 100.0
			draw_line(Vector2(0, y), Vector2(size.x, y), Color(1, 1, 1, 0.12), 1.0)
		var pts := PackedVector2Array()
		for i in values.size():
			pts.append(Vector2(size.x * float(i) / float(values.size() - 1), size.y - size.y * clampf(float(values[i]) / 100.0, 0.0, 1.0)))
		draw_polyline(pts, Color(0.35, 0.9, 1.0), 3.0)
