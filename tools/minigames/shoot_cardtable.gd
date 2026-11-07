extends SceneTree
## Entry for tools/minigames/shoot_cardtable_node.gd (the card table's shots, package A8b): the node is loaded after the first frame, when the autoloads (Session) exist.
##   bash tools/dev/godot.sh --path . --resolution 1280x720 -s tools/minigames/shoot_cardtable.gd


func _init() -> void:
	_go.call_deferred()


func _go() -> void:
	await process_frame
	root.add_child((load("res://tools/minigames/shoot_cardtable_node.gd") as GDScript).new())
