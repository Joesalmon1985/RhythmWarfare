extends SceneTree
## Tier tuning pass for the continuous run: plays RunEngine (pure logic, stepped clock, no audio) with scripted players and prints, per start node and
## accuracy, how many cues a phase asks for, how many blocks pass, and how long the run survives.
##
##   godot --headless --path . -s tools/story/tune_run.gd -- [accuracies=1.0,0.9,0.8,0.7,0.5] [seeds=3] [max_phases=12] [jitter_ms=0]
##
## A player with accuracy a hits each cue with probability a, exactly on time (plus gaussian jitter of jitter_ms when given: "sloppy" timing);
## a missed cue is simply not pressed. Every run starts on the node and always takes the default route, so depth 4 nodes loop on themselves
## (the lines for depth 1 to 3 therefore also pass through the deeper nodes; the per-node table below counts only the blocks played on that node).

func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	var accs := PackedStringArray((args[0] if args.size() > 0 else "1.0,0.9,0.8,0.7,0.5").split(","))
	var seeds := int(args[1]) if args.size() > 1 else 3
	var max_phases := int(args[2]) if args.size() > 2 else 12
	var jitter := float(args[3]) if args.size() > 3 else 0.0
	var data := RunData.load_default()
	if not data.errors.is_empty():
		print("run data errors: ", data.errors)
		quit(1)
		return
	print("node,depth,chart,accuracy,seed,cues_phase1,blocks_played,blocks_passed,mean_credit,phases_survived,final_energy,min_energy")
	var node_stats := {}  # node -> {acc -> [credit sum, blocks, passed]}
	for nid in data.node_order:
		for a_s in accs:
			var acc := float(a_s)
			for seed_i in range(1, seeds + 1):
				var r := _run(data, nid, acc, seed_i, max_phases, jitter)
				print("%s,%d,%s,%.2f,%d,%d,%d,%d,%.3f,%d,%.1f,%.1f" % [nid, int(data.nodes[nid]["depth"]), data.nodes[nid]["chart"], acc, seed_i, r["cues1"], r["blocks"], r["passed"], r["mean_credit"], r["phases"], r["energy"], r["min_energy"]])
				var key: String = nid
				if not node_stats.has(key):
					node_stats[key] = {}
				for nn in r["by_node"]:
					if not node_stats.has(nn):
						node_stats[nn] = {}
					var d: Array = node_stats[nn].get(acc, [0.0, 0, 0])
					var v: Array = r["by_node"][nn]
					node_stats[nn][acc] = [d[0] + v[0], d[1] + v[1], d[2] + v[2]]
	print("# per node over every block played on it (credit sum / blocks / passed):")
	for nn in data.node_order:
		var line := "# %s (depth %d)" % [nn, int(data.nodes[nn]["depth"])]
		for a_s in accs:
			var acc := float(a_s)
			if node_stats.get(nn, {}).has(acc):
				var d: Array = node_stats[nn][acc]
				line += "  acc %.2f: credit %.3f pass %d%% (%d blocks)" % [acc, float(d[0]) / maxf(1.0, float(d[1])), int(round(100.0 * float(d[2]) / maxf(1.0, float(d[1])))), int(d[1])]
		print(line)
	quit(0)


func _run(data: RunData, start: String, acc: float, seed_i: int, max_phases: int, jitter_ms: float) -> Dictionary:
	var e := RunEngine.new(data)
	e.begin(start)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_i * 7919 + 13
	var t := 0.0
	var step := 1.0 / 60.0
	var cursor := 0
	var planned: Array = []  # [press_time, idx]
	var releases: Array = []  # [end_time, idx, pad]
	var by_node := {}
	var blocks := 0
	var passed := 0
	var csum := 0.0
	var min_energy := e.energy
	var cues1 := 0
	var phases_done := 0
	while not e.over and e.phase_n <= max_phases:
		var evs := e.update(t)
		for ev in evs:
			if ev["kind"] == "block_result":
				blocks += 1
				csum += float(ev["credit"])
				if ev["passed"]:
					passed += 1
				var nn: String = ev["node"]
				var d: Array = by_node.get(nn, [0.0, 0, 0])
				by_node[nn] = [d[0] + float(ev["credit"]), d[1] + 1, d[2] + (1 if ev["passed"] else 0)]
				min_energy = minf(min_energy, float(ev["energy"]))
		# schedule the notes charted since the last look
		while cursor < e.level.notes.size():
			var n: Dictionary = e.level.notes[cursor]
			if rng.randf() < acc:
				var pt: float = float(n["time"]) + (rng.randfn(0.0, jitter_ms / 1000.0) if jitter_ms > 0.0 else 0.0)
				planned.append([pt, cursor])
			cursor += 1
		planned.sort_custom(func(x: Array, y: Array) -> bool: return x[0] < y[0])
		while not planned.is_empty() and float(planned[0][0]) <= t:
			var p: Array = planned.pop_front()
			var n: Dictionary = e.level.notes[int(p[1])]
			e.press(int(n["pad"]), float(p[0]), int(n["pad"]))
			releases.append([float(n["end_time"]) if n["type"] == "hold" else float(p[0]) + 0.08, int(p[1]), int(n["pad"])])
		var keep: Array = []
		for r in releases:
			if float(r[0]) <= t:
				e.release(int(r[2]), float(r[0]), int(r[2]))
			else:
				keep.append(r)
		releases = keep
		t += step
		phases_done = e.phase_n
	if cues1 == 0:
		for n in e.level.notes:
			if int(n["phase"]) == 1:
				cues1 += 1
	return {"cues1": cues1, "blocks": blocks, "passed": passed, "mean_credit": csum / maxf(1.0, float(blocks)), "phases": phases_done,
		"energy": e.energy, "min_energy": min_energy, "by_node": by_node}
