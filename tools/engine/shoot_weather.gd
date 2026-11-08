extends SceneTree
## Entry for tools/engine/shoot_weather_node.gd (the rain shot sheet, package A9): the node is loaded after the first frame, when the autoloads (Session) exist. Needs a renderer:
##   RW_RUN_VIRTUAL=1 RW_WEATHER_MAP=<path to doom_dock.json> bash tools/dev/godot.sh --resolution 1280x720 --path . -s tools/engine/shoot_weather.gd


func _init() -> void:
	_go.call_deferred()


func _go() -> void:
	await process_frame
	root.add_child((load("res://tools/engine/shoot_weather_node.gd") as GDScript).new())
