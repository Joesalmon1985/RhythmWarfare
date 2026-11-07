extends SceneTree
## Writes the baseline low-res frame of Night One (tests/fixtures/weather_frame.gd) that test_weather.gd compares a map without `weather` against. Run once, with a
## renderer (not --headless), before the weather code existed (package A9); re-run only when the world's look changes on purpose:
##   bash tools/dev/godot.sh --path . -s tests/fixtures/weather_baseline.gd


func _init() -> void:
	_go.call_deferred()


func _go() -> void:
	await process_frame
	var F: GDScript = load("res://tests/fixtures/weather_frame.gd")
	var a: Image = await F.shoot(self)
	var b: Image = await F.shoot(self)
	if a == null:
		print("no frame (headless?)")
		quit(1)
		return
	print("deterministic: ", a.get_data() == b.get_data(), " size ", a.get_size())
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://tests/fixtures/weather"))
	a.save_png(ProjectSettings.globalize_path(F.BASELINE))
	print("baseline ", F.BASELINE)
	quit(0)
