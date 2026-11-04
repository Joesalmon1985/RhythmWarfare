extends SceneTree
## Headless tuning sweep for the story thresholds:
##   godot --headless --path . -s tools/story/tune.gd -- [policy ...]
## Plays a chapter (default Night One; `chapter:mothership`) end to end with each seeded input policy (tools/autoplay.gd) and prints the ending, energy, branches
## and the player's journey (the places the rail camera was sent to, then the roles it held).

func _init() -> void:
	var policies: Array = []
	var path := StoryData.PATH
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("chapter:"):  # e.g. chapter:mothership
			path = "res://content/story/%s.json" % str(a).substr(8)
		else:
			policies.append(a)
	if policies.is_empty():
		policies = ["perfect", "accuracy:0.95", "accuracy:0.9", "accuracy:0.8", "accuracy:0.7", "accuracy:0.6", "accuracy:0.5", "beginner", "sloppy", "none"]
	for p in policies:
		for seed_value in [1, 2, 3]:
			var s := StoryRun.autoplay(str(p), 1.0 / 60.0, seed_value, {}, path)
			if s.has("errors"):
				print("ERRORS ", s["errors"])
				quit(1)
				return
			var br := ""
			for b in s["branches"]:
				br += "%s:%s " % [str(b["id"]).substr(0, 6), str(b["outcome"]).substr(0, 1)]
			var j: Dictionary = s.get("journey", {})
			print("%-14s seed %d  %-18s energy %3d peak %3d passed %2d/%d acc %.2f  %s | %s | %s" % [p, seed_value, s["ending"], int(s["energy"]), int(s["peak_energy"]),
				int(s["sequences_passed"]), int(s["sequences_total"]), float(s["accuracy"]), br, ",".join(PackedStringArray(j.get("places", []))), ",".join(PackedStringArray(j.get("roles", [])))])
	quit(0)
