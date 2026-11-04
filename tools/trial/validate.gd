extends SceneTree
## Checks the Deathtrap Dungeon's data (content/trial/*.json) and prints a summary:  godot --headless --path . -s tools/trial/validate.gd
## Add `-- all` to print every passage's links. Exit code 0 when the data is sound. Run it after adding or changing a passage (docs/TRIAL_OPENING.md).


func _initialize() -> void:
	var d := TrialData.load_default()
	for e in d.errors:
		print("ERROR ", e)
	var all := "all" in OS.get_cmdline_user_args()
	var by_status := {}
	var by_kind := {}
	var fights := 0
	var tests := 0
	for n in d.passages.keys():
		var p: Dictionary = d.passages[n]
		by_status[str(p["status"])] = int(by_status.get(str(p["status"]), 0)) + 1
		by_kind[str(p.get("kind", "normal"))] = int(by_kind.get(str(p.get("kind", "normal")), 0)) + 1
		var out: Array = []
		for c in p["choices"]:
			var dest := str(int(c["to"])) if c.get("to", null) != null else "exit"
			var tag := ""
			if c.has("encounter"):
				fights += 1
				tag = " [fight %s]" % c["encounter"]
			if c.has("test"):
				tests += 1
				tag = " [luck: %d or %d]" % [int(c["test"]["pass"]), int(c["test"]["fail"])]
			out.append("%s -> %s%s%s" % [str(c["book"]), dest, tag, " *" if bool(c.get("default", false)) else ""])
		if all or str(p["status"]) == "BOOK_VERIFIED":
			print("passage %d %s (%s): %s" % [n, p["title"], p["status"], "; ".join(PackedStringArray(out))])
	print("passages %d (+ the defeat passage 0); by status %s; by kind %s; %d fights, %d luck tests" % [d.passages.size() - 1, str(by_status), str(by_kind), fights, tests])
	print("reachable from %d: %d of 400" % [d.start, d.reachable().size()])
	print("OK" if d.errors.is_empty() else "%d problem(s)" % d.errors.size())
	quit(0 if d.errors.is_empty() else 1)
