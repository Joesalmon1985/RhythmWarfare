extends SceneTree
## Headless tuning sweep for the story thresholds:
##   godot --headless --path . -s tools/story/tune.gd -- [policy ...]
## Plays Night One end to end with each seeded input policy (tools/autoplay.gd) and prints the ending, energy and branches.

func _init() -> void:
	var policies: Array = OS.get_cmdline_user_args()
	if policies.is_empty():
		policies = ["perfect", "accuracy:0.95", "accuracy:0.9", "accuracy:0.8", "accuracy:0.7", "accuracy:0.6", "accuracy:0.5", "beginner", "sloppy", "none"]
	for p in policies:
		for seed_value in [1, 2, 3]:
			var s := StoryRun.autoplay(str(p), 1.0 / 60.0, seed_value)
			if s.has("errors"):
				print("ERRORS ", s["errors"])
				quit(1)
				return
			var br := ""
			for b in s["branches"]:
				br += "%s:%s " % [str(b["id"]).substr(0, 6), str(b["outcome"]).substr(0, 1)]
			print("%-14s seed %d  %-15s energy %3d peak %3d passed %2d/%d acc %.2f  %s" % [p, seed_value, s["ending"], int(s["energy"]), int(s["peak_energy"]),
				int(s["sequences_passed"]), int(s["sequences_total"]), float(s["accuracy"]), br])
	quit(0)
