extends SceneTree
## Entry for tools/engine/shoot_things_node.gd (the shots of world-staged things): the node is loaded after the first frame, when the autoloads (Session) exist.
##   bash tools/dev/godot.sh --path . -s tools/engine/shoot_things.gd


func _init() -> void:
	_go.call_deferred()


func _go() -> void:
	await process_frame
	root.add_child((load("res://tools/engine/shoot_things_node.gd") as GDScript).new())
