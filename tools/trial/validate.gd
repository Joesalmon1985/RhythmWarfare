extends SceneTree
## Checks the dungeon's data (content/trial/passages.json) and prints a summary:  godot --headless --path . -s tools/trial/validate.gd
## Add `-- all` to print every passage's links. Exit code 0 when the data is sound. Run it after adding or changing a passage (docs/TRIAL_OPENING.md).


func _initialize() -> void:
	var d := TrialData.load_default()
	for e in d.errors:
		print("ERROR ", e)
	var all := "all" in OS.get_cmdline_user_args()
	var counts := {"normal": 0, "death": 0, "victory": 0, "side": 0, "secret": 0}
	var fights := 0
	var tests := 0
	var gated := 0
	for n in d.passages.keys():
		var p: Dictionary = d.passages[n]
		var kind := str(p.get("kind", "normal"))
		counts[kind] = int(counts.get(kind, 0)) + 1
		if bool(p.get("side", false)):
			counts["side"] += 1
		if bool(p.get("secret", false)):
			counts["secret"] += 1
		var out: Array = []
		for c in p.get("choices", []):
			var dest := str(int(c["to"])) if c.get("to", null) != null else "exit"
			var tag := ""
			if c.has("encounter"):
				fights += 1
				tag = " [fight %s]" % c["encounter"]
			if c.has("test"):
				tests += 1
				tag = " [luck: %d or %d]" % [int(c["test"]["pass"]), int(c["test"]["fail"])]
			if c.has("requires"):
				gated += 1
				tag += " [needs %s]" % c["requires"]
			out.append("%s -> %s%s%s" % [str(c.get("label", "")), dest, tag, " *" if bool(c.get("default", false)) else ""])
		if all:
			print("passage %d %s (%s, tier %d): %s" % [n, p.get("title", ""), d.zone_name(n), int(p.get("tier", 1)), "; ".join(PackedStringArray(out))])
	print("%s: %d passages (+ the defeat passage 0) in %d zones; kinds %s; %d fights, %d luck tests, %d item-gated choices" % [str(d.raw.get("title", "")), d.passages.size() - 1, d.zones.size(), str(counts), fights, tests, gated])
	var walk := d.default_walk()
	print("the default choices walk %d passages from %d to %s" % [walk.size(), d.start, str(walk[walk.size() - 1]) if not walk.is_empty() else "nowhere"])
	print("reachable from %d: %d of %d" % [d.start, d.reachable().size(), d.passages.size() - 1])
	print("OK" if d.errors.is_empty() else "%d problem(s)" % d.errors.size())
	quit(0 if d.errors.is_empty() else 1)
