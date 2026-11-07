extends TestCase
## The run's playtest matrix, headless: scripted players of every skill (perfect, accuracy 0.9 / 0.8 / 0.7 / 0.5, sloppy, none) times seeds 1 to 3 play RunEngine with
## RunJourney on top; for each run the test records survival or depletion, the depth reached and the rail places visited, replays the journey on every world's real
## StoryPlayer and checks the camera is always in a valid sector, and checks no move starts outside the cue-free guard or lasts outside 2 to 4 bars or sits on dense cues.
## A phase is a scene (a room of a world); the run records the worlds and scenes visited, the phases survived and the rails.
## The numbers are written to user://run_matrix.txt for the docs (docs/CONTINUOUS_RUN.md).
## The route window is the hotspot window: the player taps through RunHotspots under a tap policy (RW_RUN_TAPS=scripted (default: seed 1 taps nothing, seed 2 the second exit, seed 3 a random one) |
## none (never taps: the default exits) | changed (a decoy first, then the seed's pick) | failure (scripted taps and the last block of every phase missed: every tapped hotspot fails)); the
## hotspots' cinematics are given to the journey like the scene does, so they are checked for guards, bars, density and valid sectors too. The journey's window turn (RunJourney.face_fn) is given
## like the scene gives it (StoryPlayer.best_facing over the window's hotspots), and the hotspots in the picture at beat 49 of every phase are counted.

const BPM := 174.0
const BEAT := 60.0 / 174.0
const MAX_PHASES := 20  # scenes: a path through the first three worlds is 13 to 14 phases
const POLICIES := ["perfect", "accuracy:0.9", "accuracy:0.8", "accuracy:0.7", "accuracy:0.5", "sloppy", "none"]
const STAGE_VIEW := Vector2(1280.0, 460.0)  # the stage strip of a 1280 x 720 window (the hotspot view's aspect)

var _maps: Dictionary = {}


func _map(world: String) -> StoryMap:
	if not _maps.has(world):
		_maps[world] = StoryMap.load_chapter(world)
	return _maps[world]


## One scripted run. Returns {over, phases, depth, energy, nodes, places, kinds, moves, camera_bad, dense, bad_starts, glances, log}.
func _simulate(policy: String, seed: int, data: RunData, taps := "", start := "warehouse", face := true) -> Dictionary:
	var bpm := float(data.cfg["timing"]["bpm"])  # (a path runs at its own tempo)
	var beat := 60.0 / bpm
	if OS.get_environment("RW_MATRIX_LAPS") != "":  # the matrix at another lap count (1 = the paths as they were before the two laps, for the energy comparison in docs/HANDOVER.md A12)
		for nid in data.nodes:
			(data.nodes[nid] as Dictionary)["laps"] = int(OS.get_environment("RW_MATRIX_LAPS"))
	if taps == "":
		taps = OS.get_environment("RW_RUN_TAPS") if OS.get_environment("RW_RUN_TAPS") != "" else "scripted"
	var e := RunEngine.new(data)
	e.hotspots = RunHotspots.new(data, {}, {})
	e.begin(start)
	var j := RunJourney.new(data)
	var windows: Array = []  # [{t0, node, hs}] the hotspot window of every phase, as the block-2 decision sees it
	if face:  # the run scene's window turn, with the map alone (actor anchors need the crowd: they are left out here)
		j.face_fn = func(node_id: String, _place: String) -> Array:
			var m := _map(str(data.nodes[node_id]["map"]))
			var pts: Array = []
			for h in e.hotspots.shown(3, true):
				var r := HotspotView.resolve(h["anchor"], m, {})
				if bool(r["ok"]):
					var p: Vector3 = r["pos"]
					pts.append([p.x, p.z, 1.0 if bool(h["default"]) else 0.0, p.y])
			return pts
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
	var door_done := -1
	var t := -0.5
	var max_laps := 1
	for nid in data.nodes:
		max_laps = maxi(max_laps, data.laps_of(nid))
	var end_t := float(MAX_PHASES) * e.phase_s() * float(max_laps)  # (a scene of a path plays its laps: MAX_PHASES counts scenes)
	var kinds := {}
	var places := {}
	var actions: Array = []
	var max_phase := 0
	var commits := 0
	var failures := 0
	var cinematics := 0
	while t < end_t and not e.over and e.away == "":  # (a path's ending hands the run back to the Warehouse: the simulation ends there)
		var events := e.update(t)
		for ev in events:
			if str(ev["kind"]) == "block_result" and int(ev["block"]) == 2:
				windows.append({"t0": e.phase_t0, "node": str(ev["node"]), "hs": e.hotspots.shown(3, true)})
			if str(ev["kind"]) in ["phase_start", "block_result", "lap_start"]:
				actions.append_array(j.on_event(ev, e))
			if str(ev["kind"]) == "hotspot_commit":
				var oc: Dictionary = ev["outcome"]
				commits += 1
				if not bool(oc["success"]):
					failures += 1
				if not (oc["cinematic"] as Dictionary).is_empty():
					cinematics += 1
					actions.append_array(j.hotspot_actions(oc["cinematic"], float(ev["t"]), e, Callable(), bool(oc["continued"]) or str(oc["window"]) == "early"))
			if str(ev["kind"]) == "phase_start":
				nodes.append(str(ev["node"]))
				depth = maxi(depth, int(ev["depth"]))
				max_phase = maxi(max_phase, int(ev["phase"]))
		# the player: hit or skip each cue when its time comes
		while next_i < e.level.notes.size() and float(e.level.notes[next_i]["time"]) <= t + 0.2:
			var n: Dictionary = e.level.notes[next_i]
			var hit := rng.randf() < hit_p
			if taps == "failure" and int(n["block"]) == 3:
				hit = false
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
			if taps == "changed":  # a decoy first (the other exit), then the seed's pick below
				e.choose(str((opts[opts.size() - 1] as Dictionary)["to"]))
			if taps != "none":
				if seed == 2:
					var pick := mini(1, opts.size() - 1)
					if data.is_path() and nodes.has(str((opts[pick] as Dictionary)["to"])):  # a path's setbacks lead back: never take the second arrow to a scene already played while another is new
						for k in opts.size():
							if not nodes.has(str((opts[k] as Dictionary)["to"])):
								pick = k
								break
					e.choose(str((opts[pick] as Dictionary)["to"]))
				elif seed == 3:
					e.choose(str((opts[rng.randi() % opts.size()] as Dictionary)["to"]))
		# a path inside the world: the door walk starts three beats before the phase ends (the run scene latches it once per phase)
		if e.window_open and door_done != e.phase_n and e.phase_beat_at(t) >= 61.0:
			door_done = e.phase_n
			var to := e.selected_route()
			if data.nodes.has(to) and str(data.nodes[to]["world"]) == str(data.nodes[e.node_id]["world"]) and to != e.node_id:
				actions.append_array(j.leave_walk(e.t_of(61.0), to, e))
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
			p.setup(_map(w), bpm)
			players[w] = p
		(players[w] as StoryPlayer).apply_action(a)
		if a["action"] == "player_look":
			glances += 1
		if a["action"] == "player_move" and not bool((a["args"] as Dictionary).get("cut", false)):
			moves += 1
			var bars := float((a["args"] as Dictionary)["bars"])
			if bars < 2.0 or bars > 4.0:
				bad_bars += 1
			if fposmod(float(a["t0"]) / beat, 16.0) < 12.0:
				bad_starts += 1
			if RunRail.move_is_dense(e.level.notes, float(a["t0"]), bars, bpm):
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
	# the window's hotspots in the picture at beat 49 (the window open, the turn done): how many, and the default (one at the player's feet counts: its ring is around them)
	var win_n := 0
	var win_any := 0
	var win_default := 0
	var win_all := 0
	for wdw in windows:
		var w2 := str(data.nodes[str(wdw["node"])]["map"])
		var t49 := float(wdw["t0"]) + 49.0 * BEAT
		if not players.has(w2) or t49 > t:
			continue
		var pose := (players[w2] as StoryPlayer).pose_at(t49)
		var seen := 0
		var placed := 0
		var def_seen := false
		for h in wdw["hs"]:
			var r := HotspotView.resolve(h["anchor"], _map(w2), {})
			if not bool(r["ok"]):
				continue
			placed += 1
			var pc := StoryProjector.project(r["pos"], pose, STAGE_VIEW)
			var sp: Vector2 = pc["screen"]
			var at_feet := Vector2((r["pos"] as Vector3).x, (r["pos"] as Vector3).z).distance_to(pose["pos"]) < StoryPlayer.FACE_NEAR_M  # its ring is around the player
			if at_feet or bool(pc["visible"]) and float(pc["depth"]) > 0.4 and sp.x >= 0.0 and sp.x <= STAGE_VIEW.x and sp.y >= 0.0 and sp.y <= STAGE_VIEW.y:
				seen += 1
				def_seen = def_seen or bool(h["default"])
		if placed == 0:
			continue
		win_n += 1
		win_any += 1 if seen > 0 else 0
		win_default += 1 if def_seen else 0
		win_all += 1 if seen == placed else 0
	var worlds_seen: Array = []
	for nid in nodes:
		var wid := str(data.nodes[nid]["world"])
		if worlds_seen.is_empty() or worlds_seen[worlds_seen.size() - 1] != wid:
			worlds_seen.append(wid)
	return {"worlds": worlds_seen, "over": e.over, "phases": max_phase, "depth": depth, "energy": e.energy, "nodes": nodes, "places": places, "kinds": kinds, "moves": moves, "camera_bad": camera_bad,
		"away": e.away, "samples": samples, "dense": dense, "bad_starts": bad_starts, "bad_bars": bad_bars, "glances": glances, "log": j.log, "commits": commits, "failures": failures, "cinematics": cinematics, "taps": taps,
		"windows": win_n, "win_any": win_any, "win_default": win_default, "win_all": win_all}


func test_policy_matrix_survival_depth_rails_and_camera() -> void:
	var data := RunData.load_default()
	assert_eq(data.errors, [], "run data validates")
	var rows: Array = []
	var by: Dictionary = {}
	for policy in POLICIES:
		for seed in [1, 2, 3]:
			var r := _simulate(policy, seed, data)
			by["%s/%d" % [policy, seed]] = r
			rows.append("%-13s seed %d: %s after %d phases, depth %d, energy %3.0f, %2d moves, rail %s, worlds %s, scenes %s" % [policy, seed, "ENDED   " if r["over"] else "survived", r["phases"], r["depth"], r["energy"], r["moves"],
				JSON.stringify(r["kinds"]), ">".join(PackedStringArray(r["worlds"])), ">".join(PackedStringArray(r["nodes"]))])
			var seq: Array = r["nodes"]
			for k in range(1, seq.size()):  # every step is a route of the scene before it
				var ok := false
				for e2 in data.nodes[str(seq[k - 1])]["next"]:
					ok = ok or str(e2["to"]) == str(seq[k])
				assert_true(ok, "%s seed %d: %s leads to %s" % [policy, seed, seq[k - 1], seq[k]])
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
		assert_true((p["nodes"] as Array).size() == MAX_PHASES, "and every phase is a scene (%d)" % (p["nodes"] as Array).size())
		assert_true((p["worlds"] as Array).size() >= 4, "through at least four worlds: %s" % str(p["worlds"]))
		assert_eq((p["worlds"] as Array)[0], "warehouse")
		assert_true((p["worlds"] as Array).has("hospital") or (p["worlds"] as Array).has("ward"), "the third world is reached")
		var scene_count := {}
		for nid in p["nodes"]:
			scene_count[nid] = true
		assert_true(scene_count.size() >= 8, "at least eight distinct scenes: %d" % scene_count.size())
		if OS.get_environment("RW_RUN_TAPS") != "failure":  # (the failure policy misses the last block of every phase on purpose)
			assert_eq(int((p["kinds"] as Dictionary).get("down", 0)) + int((p["kinds"] as Dictionary).get("bottom", 0)), 0, "perfect play never visits the bad rail")
		assert_true(int((p["kinds"] as Dictionary).get("up", 0)) >= 3, "perfect play climbs")
		var n: Dictionary = by["none/%d" % seed]
		assert_true(n["over"], "no play depletes the crowd (seed %d)" % seed)
		assert_true(int((n["kinds"] as Dictionary).get("bottom", 0)) >= 1, "no play reaches the bottom of the bad rail (the sick beat)")
		assert_true(int(n["phases"]) <= 4, "and the run ends within four phases (it ended in %d)" % int(n["phases"]))
		assert_eq((n["worlds"] as Array), ["warehouse"], "without leaving the Warehouse")
		assert_false(by["accuracy:0.9/%d" % seed]["over"], "accuracy 0.9 survives")
	var d9 := 0.0
	var d5 := 0.0
	for seed in [1, 2, 3]:
		d9 += float(by["accuracy:0.9/%d" % seed]["phases"])
		d5 += float(by["accuracy:0.5/%d" % seed]["phases"])
	assert_true(d9 >= d5, "better play goes at least as far as sloppy play")


## The last block turns the camera to the window's hotspots (RunJourney.window_face): at beat 49 the default exit is in the picture (or at the player's feet) in at least 85% of the windows (a few stand just under the picture, a step or two away: the camera does not tip down), and at least one hotspot in every one.
## The same runs without the turn are measured for comparison (the rail alone often faces away from the exits).
func test_the_window_opens_facing_its_hotspots() -> void:
	var data := RunData.load_default()
	var tot := {"on": [0, 0, 0, 0], "off": [0, 0, 0, 0]}
	for seed in [1, 2, 3]:
		for face in [true, false]:
			var r := _simulate("perfect", seed, data, "scripted", "warehouse", face)
			var k := "on" if face else "off"
			var a: Array = tot[k]
			a[0] += int(r["windows"])
			a[1] += int(r["win_any"])
			a[2] += int(r["win_default"])
			a[3] += int(r["win_all"])
			if face:
				assert_eq(r["camera_bad"], 0, "seed %d: the camera stays in valid sectors with the turn" % seed)
				assert_eq(int(r["win_any"]), int(r["windows"]), "seed %d: some hotspot is in the picture when every window opens (%d of %d)" % [seed, int(r["win_any"]), int(r["windows"])])
	var on: Array = tot["on"]
	var off: Array = tot["off"]
	print("  window at beat 49, with the turn: %d windows, a hotspot in view %d, the default %d, all %d; without: %d, %d, %d, %d" % [on[0], on[1], on[2], on[3], off[0], off[1], off[2], off[3]])
	assert_true(int(on[0]) >= 30, "enough windows measured (%d)" % int(on[0]))
	assert_true(float(on[2]) >= 0.85 * float(on[0]), "the default exit is in the picture (or at the player's feet) in at least 85%% of the windows (%d of %d)" % [int(on[2]), int(on[0])])
	assert_true(int(on[2]) > int(off[2]) and int(on[3]) > int(off[3]), "the turn frames more of them than the rail alone")


func test_tap_policies_commit_inside_the_guard_and_keep_every_journey_valid() -> void:
	var data := RunData.load_default()
	for taps in ["none", "scripted", "changed", "failure"]:
		for policy in ["perfect", "accuracy:0.8"]:
			var r := _simulate(policy, 3, data, taps)
			var tag := "%s taps, %s" % [taps, policy]
			assert_eq(r["camera_bad"], 0, "%s: the camera is always in a valid sector" % tag)
			assert_eq(r["bad_starts"], 0, "%s: every move (cinematics included) starts in a cue-free guard" % tag)
			assert_eq(r["bad_bars"], 0, "%s: every move lasts 2 to 4 bars" % tag)
			assert_eq(r["dense"], 0, "%s: no move sits on dense cues" % tag)
			assert_true(int(r["commits"]) >= 1, "%s: hotspots commit (%d)" % [tag, int(r["commits"])])
			var seq: Array = r["nodes"]
			for k in range(1, seq.size()):
				var ok := false
				for e2 in data.nodes[str(seq[k - 1])]["next"]:
					ok = ok or str(e2["to"]) == str(seq[k])
				assert_true(ok, "%s: %s leads to %s" % [tag, seq[k - 1], seq[k]])
			if taps == "failure" and policy == "perfect":
				assert_true(int(r["failures"]) >= 1, "failure taps: the tapped hotspots fail (%d of %d)" % [int(r["failures"]), int(r["commits"])])
			if taps == "scripted" and policy == "perfect":
				assert_eq(int(r["failures"]), 0, "perfect play passes every last block")


## The matrix once per path (content/paths/<id>): every tap policy against four skills, the same checks on the journeys (guards, bars, density, the camera in a valid sector) at the path's own
## tempo; a perfect player reaches an ending and is handed back to the Warehouse (the simulation ends at the handoff), nobody ever skips a scene that is not a route of the one before.
func test_policy_matrix_on_every_path_under_every_tap_policy() -> void:
	var ids: Array = []
	for pid in RunData.path_ids():
		if RunData.path_exists(str(pid)):
			ids.append(pid)
	assert_true(ids.has("stub"), "the stub path is there: %s" % str(ids))
	var rows: Array = []
	for pid in ids:
		var data := RunData.load_path(str(pid))
		assert_eq(data.errors, [], "path %s validates" % pid)
		var bpm := float(data.cfg["timing"]["bpm"])
		for taps in ["none", "scripted", "changed", "failure"]:
			for policy in ["perfect", "accuracy:0.8", "sloppy", "none"]:
				var r := _simulate(policy, 2, data, taps, data.start_node())
				var tag := "path %s, %s taps, %s" % [pid, taps, policy]
				rows.append("%-8s %-9s %-13s %s after %2d scenes (%2d phases), away %s, energy %3.0f, scenes %s" % [pid, taps, policy, "ENDED   " if r["over"] else "survived", (r["nodes"] as Array).size(), r["phases"], r["away"], r["energy"], ">".join(PackedStringArray(r["nodes"]))])
				assert_eq(r["camera_bad"], 0, "%s: the camera is always in a valid sector" % tag)
				assert_eq(r["bad_starts"], 0, "%s: every move starts in a cue-free guard" % tag)
				assert_eq(r["bad_bars"], 0, "%s: every move lasts 2 to 4 bars" % tag)
				assert_eq(r["dense"], 0, "%s: no move sits on dense cues" % tag)
				var seq: Array = r["nodes"]
				assert_eq(seq[0], data.start_node(), "%s: it begins at the start scene" % tag)
				for k in range(1, seq.size()):
					var ok := false
					for e2 in data.nodes[str(seq[k - 1])]["next"]:
						ok = ok or str(e2["to"]) == str(seq[k])
					ok = ok or (seq[k - 1] == seq[k] and bool(data.nodes[str(seq[k])].get("relaxed", false)))  # (a relaxed node, H1.7, stays: its next phase is the same scene)
					assert_true(ok, "%s: %s leads to %s" % [tag, seq[k - 1], seq[k]])
				# a path may own a loop (the Mission Count's endless missions, route marked `loop`): a player who never touches its way out lives in it for as long as the crowd stays, which is the design
				var has_loop := false
				for nid in data.nodes:
					for e3 in data.nodes[nid]["next"]:
						has_loop = has_loop or bool(e3.get("loop", false))
					has_loop = has_loop or bool((data.nodes[nid] as Dictionary).get("relaxed", false))  # (a relaxed node, H1.7, is a loop by design: nothing touched stays)
				var lives_in_loop: bool = has_loop and seq.size() > 1 and seq.size() != _unique(seq).size() and taps in ["none", "failure"]
				assert_true(bool(r["over"]) or str(r["away"]) == "run:warehouse" or lives_in_loop, "%s: the path ends by the crowd leaving or by the way back to the Warehouse (%s)" % [tag, str(r["away"])])
				if policy == "perfect" and taps != "failure" and not lives_in_loop:
					assert_eq(str(r["away"]), "run:warehouse", "%s: perfect play reaches an ending and is handed back" % tag)
					assert_true(str(data.nodes[str(seq[seq.size() - 1])]["ending"]) != "", "%s: the last scene is an ending" % tag)
				assert_true(absf(bpm - float(data.cfg["timing"]["bpm"])) < 1e-9)
	var f := FileAccess.open("user://run_matrix_paths%s.txt" % ("_laps" + OS.get_environment("RW_MATRIX_LAPS") if OS.get_environment("RW_MATRIX_LAPS") != "" else ""), FileAccess.WRITE)
	f.store_string("\n".join(PackedStringArray(rows)) + "\n")
	f.close()


func _unique(a: Array) -> Array:
	var out: Array = []
	for x in a:
		if not out.has(x):
			out.append(x)
	return out
