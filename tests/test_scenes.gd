extends TestCase
## Every scene and UI script parses and loads (a parse error in a menu would otherwise only show when it opens).


func test_every_scene_and_ui_script_loads() -> void:
	for dir_path in ["res://src/scenes", "res://src/ui"]:
		var dir := DirAccess.open(dir_path)
		for name in dir.get_files():
			if name.ends_with(".gd") or name.ends_with(".tscn"):
				var res: Resource = load(dir_path.path_join(name))
				assert_true(res != null, "%s loads" % name)
				if res is PackedScene:
					assert_true((res as PackedScene).can_instantiate(), "%s instantiates" % name)


func test_pad_key_labels_match_the_input_map() -> void:
	assert_eq([PadView.key_name(1), PadView.key_name(2), PadView.key_name(3), PadView.key_name(4)], ["D", "F", "J", "K"])
