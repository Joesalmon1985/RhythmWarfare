extends SceneTree
## Checks content/trial/passages.json and prints the link map:  godot --headless --path . -s tools/trial/validate.gd
## Exit code 0 when the data is sound. Run it after adding a passage (docs/TRIAL_OPENING.md).


func _initialize() -> void:
	var d := TrialData.load_default()
	for e in d.errors:
		print("ERROR ", e)
	for n in d.passages.keys():
		var p: Dictionary = d.passages[n]
		var out: Array = []
		for c in p["choices"]:
			var dest := str(int(c["to"])) if c.get("to", null) != null else "exit"
			var fight := " [fight %s]" % c["encounter"] if c.has("encounter") else ""
			out.append("%s -> %s%s" % [str(c["book"]), dest, fight])
		print("passage %d %s (%s): %s" % [n, p["title"], p["status"], "; ".join(PackedStringArray(out))])
	print("reachable from %d: %s" % [d.start, str(d.reachable())])
	print("OK" if d.errors.is_empty() else "%d problem(s)" % d.errors.size())
	quit(0 if d.errors.is_empty() else 1)
