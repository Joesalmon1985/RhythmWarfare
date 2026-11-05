extends SceneTree
## The energy economy of the two laps (docs/HANDOVER.md A12): a path played by a scripted player of a given accuracy (every cue hit with that probability, on time), default exits, over several seeds, with the
## scenes at the laps the data says and at one lap. Prints, per accuracy, how many runs reach an ending, how many scenes and blocks they get through, the mean crowd energy at the end of each scene and its lowest value.
## Judgement, tap windows and energy numbers are the single phase's in both: only the number of blocks per scene differs.
##
##   godot --headless --path . -s tools/run/laps_energy.gd -- gospel [seeds [accuracies, e.g. 0.52,0.56,0.6]]        (squadron, ember, stub)

const ACCURACIES := [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var pid := args[0] if args.size() > 0 else "gospel"
	var seeds := int(args[1]) if args.size() > 1 else 12
	var accs: Array = ACCURACIES
	if args.size() > 2:
		accs = []
		for a in args[2].split(",", false):
			accs.append(float(a))
	print("energy economy of %s, %d seeds per accuracy, default exits, scripted hits" % [pid, seeds])
	print("%-9s %-14s %8s %8s %8s %9s %9s" % ["accuracy", "laps", "reached", "scenes", "blocks", "mean E", "min E"])
	for p in accs:
		for mode in [1, 0]:
			var reached := 0
			var scenes := 0
			var blocks := 0
			var e_sum := 0.0
			var e_n := 0
			var e_min := 100.0
			for s in seeds:
				var r := _run(pid, p, s + 1, mode)
				reached += 1 if str(r["away"]) == "run:warehouse" else 0
				scenes += int(r["scenes"])
				blocks += int(r["blocks"])
				e_sum += float(r["e_sum"])
				e_n += int(r["e_n"])
				e_min = minf(e_min, float(r["e_min"]))
			print("%-9.2f %-14s %5d/%-2d %8.1f %8.1f %9.1f %9.1f" % [p, "one lap" if mode == 1 else "as the data", reached, seeds, float(scenes) / seeds, float(blocks) / seeds, e_sum / maxf(e_n, 1), e_min])
	quit()


func _run(pid: String, accuracy: float, seed: int, mode: int) -> Dictionary:
	var data := RunData.load_path(pid)
	if mode == 1:
		for nid in data.nodes:
			(data.nodes[nid] as Dictionary)["laps"] = 1
	var e := RunEngine.new(data)
	e.hotspots = RunHotspots.new(data, {}, {})
	e.begin(data.start_node())
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var plan := {}
	var next_i := 0
	var t := -0.5
	var blocks := 0
	var e_sum := 0.0
	var e_n := 0
	var e_min := 100.0
	var scenes := 1
	while t < 3000.0 and not e.over and e.away == "":
		for ev in e.update(t):
			match str(ev["kind"]):
				"block_result":
					blocks += 1
					e_min = minf(e_min, float(ev["energy"]))
				"phase_start":
					if int(ev["phase"]) > 1 and str(ev["from"]) != "":
						scenes += 1
						e_sum += e.energy
						e_n += 1
		while next_i < e.level.notes.size() and float(e.level.notes[next_i]["time"]) <= t + 0.2:
			plan[next_i] = rng.randf() < accuracy
			next_i += 1
		for i in plan.keys():
			var n: Dictionary = e.level.notes[i]
			if plan[i] is bool:
				if bool(plan[i]) and float(n["time"]) <= t:
					e.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
					plan[i] = {"up": float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.06}
				elif not bool(plan[i]) and float(n["time"]) < t - 1.0:
					plan.erase(i)
			elif float((plan[i] as Dictionary)["up"]) <= t:
				e.release(int(n["pad"]), float((plan[i] as Dictionary)["up"]), int(n["pad"]))
				plan.erase(i)
		t += 1.0 / 30.0
	return {"away": e.away, "scenes": scenes, "blocks": blocks, "e_sum": e_sum, "e_n": e_n, "e_min": e_min}
