extends SceneTree
## Loads the Mission Count's run, its three maps and their chapter data and prints every error: `godot --headless --path . -s tools/paths/check_squadron.gd`
func _init() -> void:
	var bad := 0
	var d := RunData.load_path("squadron")
	print("run: %d scenes, %d errors, %d warnings" % [d.nodes.size(), d.errors.size(), d.warnings.size()])
	for e in d.errors:
		print("  ERROR ", e)
		bad += 1
	for w in d.warnings:
		print("  warn ", w)
	for m in ["airfield", "city", "harbour"]:
		var sd: StoryData = StoryData.load_file("res://content/story/%s.json" % m)["data"]
		var map := StoryMap.load_chapter(m)
		map.validate_chapter(sd.raw)
		print("map %s: %d sectors, %d things, %d homes, %d errors" % [m, map.sectors.size(), map.things.size(), map.homes.size(), map.errors.size()])
		for e in map.errors:
			print("  ERROR ", e)
			bad += 1
		var assets := StoryAssets.load_art(sd.art)
		sd.validate_art(assets, [])
		for a in sd.actors:
			if assets.rig(str(a["archetype"]), str(a["variant"]), str(a.get("art", ""))).is_empty():
				print("  ERROR no rig for ", a["id"])
				bad += 1
	quit(1 if bad > 0 else 0)
