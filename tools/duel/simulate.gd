extends SceneTree
## Plays scripted duels between two bots with no window and no waiting (song time is stepped), to tune duel.json.
##   godot --headless --path . -s tools/duel/simulate.gd -- [matches] [skill_a] [skill_b]
## skills: apprentice | adept | archmage | perfect. Prints, per pairing, A's wins, B's wins, draws and the mean/min/max length in phrases and seconds.

const STEP := 1.0 / 60.0


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var matches := int(args[0]) if args.size() > 0 else 30
	var pairs: Array = []
	if args.size() >= 3:
		pairs.append([args[1], args[2]])
	else:
		pairs = [["archmage", "archmage"], ["adept", "adept"], ["archmage", "adept"], ["adept", "apprentice"], ["archmage", "apprentice"], ["apprentice", "apprentice"], ["perfect", "perfect"]]
	var rules := DuelRules.load_default()
	var rdata := RunData.load_default()
	if not rules.errors.is_empty() or not rdata.errors.is_empty():
		print("data errors: ", rules.errors, rdata.errors)
		quit(1)
		return
	for p in pairs:
		var wins := [0, 0, 0]
		var lens: Array = []
		var reasons := {}
		for m in matches:
			var r := play(rules, rdata, str(p[0]), str(p[1]), 1000 + m * 17)
			wins[0 if r["winner"] == 0 else (1 if r["winner"] == 1 else 2)] += 1
			lens.append(int(r["phrases"]))
			reasons[r["reason"]] = int(reasons.get(r["reason"], 0)) + 1
		var total := 0
		for l in lens:
			total += int(l)
		var mean := float(total) / float(lens.size())
		var secs := mean * 8.0 * 60.0 / 174.0
		print("%-10s vs %-10s  A %2d  B %2d  draw %2d   phrases mean %.1f (%d..%d)  ~%.0f s   %s" % [p[0], p[1], wins[0], wins[1], wins[2], mean, lens.min(), lens.max(), secs, str(reasons)])
	quit(0)


func make_bot(rules: DuelRules, skill: String, seed_value: int) -> DuelBot:
	var b := DuelBot.from_skill(rules, skill if skill != "perfect" else "archmage", seed_value)
	if skill == "perfect":
		b.hit = 1.0
		b.sigma_ms = 0.0
		b.strays = 0.0
	return b


func play(rules: DuelRules, rdata: RunData, skill_a: String, skill_b: String, seed_value: int) -> Dictionary:
	var ea := DuelEngine.new(rules, rdata)
	var eb := DuelEngine.new(rules, rdata)
	ea.begin()
	eb.begin()
	var ba := make_bot(rules, skill_a, seed_value)
	var bb := make_bot(rules, skill_b, seed_value + 1)
	var duel := DuelMatch.new(rules)
	var t := -ea.count_in_s()
	var limit := float(int(rules.cfg["max_phrases"]) + int(rules.cfg["sudden_death_extra"]) + 4) * ea.phrase_s()
	while not duel.finished and t < limit:
		t += STEP
		ba.step(ea, t)
		bb.step(eb, t)
		for ev in ea.update(t):
			if str(ev["kind"]) == "result":
				duel.submit(0, int(ev["j"]), ev)
		for ev in eb.update(t):
			if str(ev["kind"]) == "result":
				duel.submit(1, int(ev["j"]), ev)
	return {"winner": duel.winner, "reason": duel.reason, "phrases": duel.phrase, "hp10": duel.hp10}
