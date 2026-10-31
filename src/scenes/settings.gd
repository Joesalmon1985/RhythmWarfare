extends Control
## The Settings screen: the shared settings panel, back to Home when closed.


func _ready() -> void:
	theme = UiStyle.theme()
	var panel := SettingsPanel.new()
	panel.closed.connect(func() -> void: get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn"))
	add_child(panel)


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		get_tree().change_scene_to_file("res://src/scenes/main_menu.tscn")
