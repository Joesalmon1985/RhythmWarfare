extends TestCase
## The run's playtest matrix, headless: scripted players of every skill (perfect, accuracy 0.9 / 0.8 / 0.7 / 0.5, sloppy, none) times seeds 1 to 3 play RunEngine with
## RunJourney on top; for each run the test records survival or depletion, the depth reached and the rail places visited, replays the journey on every world's real
## StoryPlayer and checks the camera is always in a valid sector, and checks no move starts outside the cue-free guard or lasts outside 2 to 4 bars or sits on dense cues.
## The numbers are written to user://run_matrix.txt for the docs (docs/CONTINUOUS_RUN.md).

const BPM := 174.0
const BEAT := 60.0 / 174.0
const MAX_PHASES := 8
const POLICIES := ["perfect", "accuracy:0.9", "accuracy:0.8", "accuracy:0.7", "accuracy:0.5", "sloppy", "none"]

var _maps: Dictionary = {}


func _map(world: String) -> StoryMap:
	if not _maps.has(world):
		_maps[world] = StoryMap.load_chapter(world)
	return _maps[world]


## One scripted run. Returns {over, phases, depth, energy, nodes, places, kinds, moves, camera_bad, dense, bad_starts, glances, log}.
func _simulate(policy: String, seed: int, data: RunData) -> Dictionary:
	var e := RunEngine.new(data)
	e.begin("warehouse")
	var j := RunJourney.new(data)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var hit_p := 1.0
	var jitter := 0.0
	match policy:
		"perfect":
			hit_p = 1.0
		"none":
			hit_p = 0.0
		"sloppy":
			hit_p = 0.8
			jitter = 0.11
		_:
			hit_p = float(policy.get_slice(":", 1))
	var next_i := 0
	var pressed: Array = []  # [{i, end}] holds being held
	var plan: Dictionary = {}  # note index -> {hit, at}
	var depth := 1
	var nodes: Array = []
	var routes_done := {}
	var t := -0.5
	var end_t := float(MAX_PHASES) * e.phase_s()
	var kinds := {}
	var places := {}
	var actions: Array = []
	var max_phase := 0
	while t < end_t and not e.over:
		var events := e.update(t)
		for ev in events:
			if str(ev["kind"]) in ["phase_start", "block_result"]:
				actions.append_array(j.on_event(ev, e))
			if str(ev["kind"]) == "phase_start":
				nodes.append(str(ev["node"]))
				depth = maxi(depth, int(ev["depth"]))
				max_phase = maxi(max_phase, int(ev["phase"]))
		# the player: hit or skip each cue when its time comes
		while next_i < e.level.notes.size() and float(e.level.notes[next_i]["time"]) <= t + 0.2:
			var n: Dictionary = e.level.notes[next_i]
			var hit := rng.randf() < hit_p
			var at := float(n["time"]) + (rng.randf_range(-jitter, jitter) if jitter > 0.0 else 0.0)
			plan[next_i] = {"hit": hit, "at": at}
			next_i += 1
		for i in plan.keys():
			var pl: Dictionary = plan[i]
			if pl["hit"] and not pl.has("down") and float(pl["at"]) <= t:
				pl["down"] = true
				e.press(int(e.level.notes[i]["pad"]), float(pl["at"]), int(e.level.notes[i]["pad"]))
			if pl.has("down"):
				var n2: Dictionary = e.level.notes[i]
				var up_t := float(n2["end_time"]) if n2["type"] == "hold" else float(pl["at"]) + 0.06
				if up_t <= t and not pl.has("up"):
					pl["up"] = true
					e.release(int(n2["pad"]), up_t, int(n2["pad"]))
			if pl.has("up") or (not pl["hit"] and float(pl["at"]) < t - 1.0):
				plan.erase(i)
		# route choice per seed: 1 keeps the default, 2 takes the second arrow, 3 picks at random
		if e.window_open and not routes_done.has(e.phase_n) and e.phase_beat_at(t) > 52.0:
			routes_done[e.phase_n] = true
			var opts := e.options()
			if seed == 2:
				e.choose(str((opts[1] as Dictionary)["to"]))
			elif seed == 3:
				e.choose(str((opts[rng.randi() % opts.size()] as Dictionary)["to"]))
		t += 1.0 / 30.0
	for entry in j.log:
		kinds[entry["kind"]] = int(kinds.get(entry["kind"], 0)) + 1
		places["%s:%s" % [entry["node"], entry["place"]]] = true
	# the journey replayed on each world's real rail camera
	var players: Dictionary = {}
	var moves := 0
	var bad_starts := 0
	var dense := 0
	var bad_bars := 0
	var glances := 0
	for a in actions:
		var w := str(a["world"])
		if not players.has(w):
			var p := StoryPlayer.new()
			p.setup(_map(w), BPM)
			players[w] = p
		(players[w] as StoryPlayer).apply_action(a)
		if a["action"] == "player_look":
			glances += 1
		if a["action"] == "player_move" and not bool((a["args"] as Dictionary).get("cut", false)):
			moves += 1
			var bars := float((a["args"] as Dictionary)["bars"])
			if bars < 2.0 or bars > 4.0:
				bad_bars += 1
			if fposmod(float(a["t0"]) / BEAT, 16.0) < 12.0:
				bad_starts += 1
			if RunRail.move_is_dense(e.level.notes, float(a["t0"]), bars, BPM):
				dense += 1
	var camera_bad := 0
	var samples := 0
	for w in players:
		var m := _map(w)
		var p2: StoryPlayer = players[w]
		var s := 0.0
		while s < t + 4.0:
			var pose := p2.pose_at(s)
			samples += 1
			if m.sector(str(pose["sector"])).is_empty() or m.sector_at(Vector2(pose["pos"])) == "" or (p2.errors as Array).size() > 0:
				camera_bad += 1
			s += 0.25
	return {"over": e.over, "phases": max_phase, "depth": depth, "energy": e.energy, "nodes": nodes, "places": places, "kinds": kinds, "moves": moves, "camera_bad": camera_bad,
		"samples": samples, "dense": dense, "bad_starts": bad_starts, "bad_bars": bad_bars, "glances": glances, "log": j.log}


func test_policy_matrix_survival_depth_rails_and_camera() -> void:
	var data := RunData.load_default()
	assert_eq(data.errors, [], "run data validates")
	var rows: Array = []
	var by: Dictionary = {}
	for policy in POLICIES:
		for seed in [1, 2, 3]:
			var r := _simulate(policy, seed, data)
			by["%s/%d" % [policy, seed]] = r
			rows.append("%-13s seed %d: %s after %d phases, depth %d, energy %3.0f, %2d moves, rail %s, route %s" % [policy, seed, "ENDED   " if r["over"] else "survived", r["phases"], r["depth"], r["energy"], r["moves"],
				JSON.stringify(r["kinds"]), "/".join(PackedStringArray(r["nodes"]))])
			assert_eq(r["camera_bad"], 0, "%s seed %d: the camera is always in a valid sector (%d of %d samples)" % [policy, seed, r["camera_bad"], r["samples"]])
			assert_eq(r["bad_starts"], 0, "%s seed %d: every move starts in a cue-free guard" % [policy, seed])
			assert_eq(r["bad_bars"], 0, "%s seed %d: every move lasts 2 to 4 bars" % [policy, seed])
			assert_eq(r["dense"], 0, "%s seed %d: no move sits on dense cues (the dense-run warning stays silent)" % [policy, seed])
			var blocks: int = (r["log"] as Array).size()  # blocks actually judged (a run that ends mid-phase has fewer than phases * 4)
			assert_true(int(r["glances"]) >= blocks - 1, "%s seed %d: a glance in every block (%d glances, %d blocks)" % [policy, seed, int(r["glances"]), blocks])
	var f := FileAccess.open("user://run_matrix.txt", FileAccess.WRITE)
	f.store_string("\n".join(PackedStringArray(rows)) + "\n")
	f.close()
	for seed in [1, 2, 3]:
		var p: Dictionary = by["perfect/%d" % seed]
		assert_false(p["over"], "perfect play survives all %d phases" % MAX_PHASES)
		assert_eq(p["depth"], 4, "and reaches the last depth")
		assert_eq(int((p["kinds"] as Dictionary).get("down", 0)) + int((p["kinds"] as Dictionary).get("bottom", 0)), 0, "perfect play never visits the bad rail")
		assert_true(int((p["kinds"] as Dictionary).get("up", 0)) >= 3, "perfect play climbs")
		var n: Dictionary = by["none/%d" % seed]
		assert_true(n["over"], "no play depletes the crowd (seed %d)" % seed)
		assert_true(int((n["kinds"] as Dictionary).get("bottom", 0)) >= 1, "no play reaches the bottom of the bad rail (the sick beat)")
		assert_true(int(n["phases"]) <= 4, "and the run ends within four phases (it ended in %d)" % int(n["phases"]))
		assert_false(by["accuracy:0.9/%d" % seed]["over"], "accuracy 0.9 survives")
	var d9 := 0.0
	var d5 := 0.0
	for seed in [1, 2, 3]:
		d9 += float(by["accuracy:0.9/%d" % seed]["phases"])
		d5 += float(by["accuracy:0.5/%d" % seed]["phases"])
	assert_true(d9 >= d5, "better play goes at least as far as sloppy play")
