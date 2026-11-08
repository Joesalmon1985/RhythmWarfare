extends SceneTree
## The race's balance at a glance (docs/bedsit/RACE.md "Calibration"): plays the Space race with the pure simulation under a grid of rhythm qualities and driver policies
## and prints position, time, contacts and overtakes.  bash tools/dev/godot.sh --headless --path . -s tools/race/calibrate_race.gd [-- <seed> ...]


func _init() -> void:
	var seeds: Array = []
	for a in OS.get_cmdline_user_args():
		seeds.append(int(a))
	if seeds.is_empty():
		seeds = [7, 11, 23]
	var Bot: GDScript = load("res://tests/fixtures/race_bot.gd")
	for seed: int in seeds:
		for q: float in [1.0, 0.8, 0.6, 0.3, 0.0]:
			for drive: String in ["best", "none", "worst"]:
				var a: Variant = Bot.play(Bot.make(seed), drive, q)
				print("seed %d  rhythm %.1f  %-5s  %s" % [seed, q, drive, JSON.stringify(Bot.summary(a))])
	quit(0)
