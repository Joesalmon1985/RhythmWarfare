extends SceneTree
## The energy economy of track scenes (docs/RUN_TRACK_SCENES.md "Energy"), the A12 method (tools/run/laps_energy.gd): the main run played by scripted players of a given cue accuracy (every cue hit with
## that probability, on time), default exits, over several seeds; once as today (ordinary scenes) and once with EVERY scene a track scene on synthetic packs that look like the real normal charts
## (about 7 cues a block, one block in seven empty, 4 laps a scene at 165 to 178 BPM). Prints per accuracy: scenes survived (mean, and how many runs reached the cap), blocks, mean and min energy.
##
##   godot --headless --path . -s tests/fixtures/track_scenes/track_energy.gd -- <seeds> <accuracies> <cap scenes> <modes: today,track> [pass_gain,pass_bonus,fail_loss,fail_flat]

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")
const PACKS := 6


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var seeds := int(args[0]) if args.size() > 0 else 8
	var accs: Array = []
	for a in (args[1] if args.size() > 1 else "0.4,0.5,0.6,0.7").split(",", false):
		accs.append(float(a))
	var cap := int(args[2]) if args.size() > 2 else 30
	var modes: Array = Array((args[3] if args.size() > 3 else "today,track").split(",", false))
	var nums: Array = []
	if args.size() > 4:
		for x in args[4].split(",", false):
			nums.append(float(x))
	Fx.clear()
	for i in PACKS:
		var gaps: Array = []
		for g in range(40 + 4 * (i % 3), 130, 28):  # one empty block in seven
			gaps.append([g, g + 4])
		Fx.write_pack("sim_%d" % i, {"bpm": 165.0 + 2.6 * float(i), "bars": 216, "cue_bars": [30, 140], "step_beats": 2, "gap_bars": gaps,
			"sections": [["intro", "intro", 0, 56], ["d1", "drop", 56, 96], ["b", "breakdown", 96, 152], ["d2", "drop", 152, 200]]})
	print("track energy: %d seeds, cap %d scenes, track numbers %s" % [seeds, cap, str(nums) if not nums.is_empty() else "(run.json)"])
	print("%-6s %-6s %8s %8s %8s %8s %8s %8s" % ["acc", "mode", "scenes", "at cap", "blocks", "meanE", "minE", "s.d."])
	for p in accs:
		for mode in modes:
			var sc: Array = []
			var capped := 0
			var blocks := 0
			var e_sum := 0.0
			var e_n := 0
			var e_min := 100.0
			for s in seeds:
				var r := _run(str(mode), p, s + 1, cap, nums)
				sc.append(int(r["scenes"]))
				capped += 1 if bool(r["capped"]) else 0
				blocks += int(r["blocks"])
				e_sum += float(r["e_sum"])
				e_n += int(r["e_n"])
				e_min = minf(e_min, float(r["e_min"]))
			var mean := 0.0
			for x in sc:
				mean += float(x)
			mean /= float(sc.size())
			var var_ := 0.0
			for x in sc:
				var_ += (float(x) - mean) * (float(x) - mean)
			print("%-6.2f %-6s %8.1f %5d/%-2d %8.1f %8.1f %8.1f %8.1f" % [p, mode, mean, capped, seeds, float(blocks) / seeds, e_sum / maxf(e_n, 1), e_min, sqrt(var_ / float(sc.size()))])
	Fx.clear()
	quit()


func _run(mode: String, accuracy: float, seed: int, cap: int, nums: Array) -> Dictionary:
	var d: RunData
	if mode == "track":
		var main := {}
		var data0 := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, seed)
		var k := 0
		for nid in data0.node_order:
			main[nid] = {"track": "sim_%d" % (k % PACKS)}
			k += 1
		d = Fx.main_data({"main": main}, seed)
		if not nums.is_empty():
			d.cfg["energy"]["track"] = {"pass_gain": nums[0], "pass_bonus": nums[1], "fail_loss": nums[2], "fail_flat": nums[3]}
	else:
		d = RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, seed)
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin(d.start_node())
	var rng := RandomNumberGenerator.new()
	rng.seed = seed * 7919 + int(accuracy * 1000.0)
	var plan := {}
	var next_i := 0
	var t := -0.5
	var blocks := 0
	var e_sum := 0.0
	var e_n := 0
	var e_min := 100.0
	while not e.over and e.scene_index() <= cap:
		for ev in e.update(t):
			match str(ev["kind"]):
				"block_result":
					blocks += 1
					e_min = minf(e_min, float(ev["energy"]))
				"phase_start":
					if int(ev["phase"]) > 1:
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
		t += 1.0 / 20.0
	return {"scenes": e.scene_index() - (0 if e.over else 1), "capped": not e.over, "blocks": blocks, "e_sum": e_sum, "e_n": e_n, "e_min": e_min}
