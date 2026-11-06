extends TestCase
## Two laps per path scene (docs/CONTINUOUS_RUN.md "Two laps", docs/HANDOVER.md A12). A scene of a path plays `laps` 64-beat phases in a row; only the LAST lap carries the hotspot window, the route window and
## the commit; the bass already in stays in across the lap boundary (no strip-back, no restart of any voice); the per-block rules (judgement, energy) are the single phase's; the cast counts beats across
## the laps; the tempo handoff, the cues' grid and the 174 BPM main run are as they were.

const TMP_SAVE := "user://test_laps_save.json"

var _saved: RunProgress = null


# --- helpers ---------------------------------------------------------------------------------------------------------------------

func _engine(d: RunData, start: String, run_flags: Dictionary = {}) -> RunEngine:
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, run_flags, {})
	e.begin(start)
	return e


## Perfect hits except the blocks named in `miss` ([[phase, block], ...] by the engine's own phase numbers: every lap is a phase). Runs until the engine has entered scene number `until_scene`
## (exclusive: 2 = the first scene is over), has handed off, or has ended. `step` is the frame step; `at` is called with (engine, t) every frame (taps, leaving). Returns every event.
func _play(e: RunEngine, until_scene := 2, miss: Array = [], step := 1.0 / 30.0, at: Callable = Callable()) -> Array:
	var log: Array = []
	var pressed := {}
	var released := {}
	var t := -0.5
	var guard := 0
	while e.scene_index() < until_scene and not e.over and e.away == "" and guard < 60000:
		guard += 1
		log.append_array(e.update(t))
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			var skip := false
			for m in miss:
				if int(n["phase"]) == int(m[0]) and int(n["block"]) == int(m[1]):
					skip = true
			if skip:
				continue
			if not pressed.has(i) and float(n["time"]) <= t:
				pressed[i] = true
				e.press(int(n["pad"]), float(n["time"]))
			if pressed.has(i) and n["type"] == "hold" and not released.has(i) and float(n["end_time"]) <= t:
				released[i] = true
				e.release(int(n["pad"]), float(n["end_time"]))
		if at.is_valid():
			at.call(e, t)
		t += step
	return log


func _of(log: Array, kind: String) -> Array:
	return log.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == kind)


func _stages_never_lowered(mixes: Array) -> bool:
	var last := 0
	for m in mixes:
		if int(m["stage"]) < last:
			return false
		last = int(m["stage"])
	return true


func _isolate_save() -> void:
	_saved = Session.run_progress
	DirAccess.remove_absolute(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")


func _restore_save() -> void:
	if _saved != null:
		Session.run_progress = _saved
		_saved = null
	DirAccess.remove_absolute(TMP_SAVE)


func _scene(env: Dictionary, size := Vector2(844, 390)) -> Dictionary:
	_isolate_save()
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	for k in env:
		OS.set_environment(str(k), str(env[k]))
	Session.run_start_node = ""
	Session.run_start_path = ""
	var host := Control.new()
	host.size = size
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = size
	return {"host": host, "scene": scene, "env": env.keys()}


func _free(d: Dictionary) -> void:
	_restore_save()
	(d["host"] as Control).queue_free()
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_RUN_START", "RW_RUN_PATH", "RW_RUN_TAPS", "RW_RUN_FLAGS"]:
		OS.unset_environment(k)


func _run_until(scene: Node, t_end: float, stop: Callable) -> void:
	var t: float = scene._vt
	while t < t_end and not stop.call():
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


# --- the data --------------------------------------------------------------------------------------------------------------------

const SINGLE := {"gospel": ["jordan", "jerusalem.golgotha"], "squadron": [], "ember": ["hollow"]}


func test_every_scene_of_the_three_paths_plays_two_laps_except_the_named_ones() -> void:
	for pid in SINGLE:
		var d := RunData.load_path(str(pid))
		assert_eq(d.errors, [], "%s validates" % pid)
		assert_eq(int(d.path_info["laps"]), 2, "%s: path.laps" % pid)
		var twos := 0
		for id in d.nodes:
			var want := 1 if (SINGLE[pid] as Array).has(id) else 2
			assert_eq(d.laps_of(str(id)), want, "%s %s plays %d lap(s)" % [pid, id, want])
			twos += 1 if want == 2 else 0
		assert_true(twos >= 14, "%s: %d two-lap scenes" % [pid, twos])
	var gd := RunData.load_path("gospel")
	assert_true(str(gd.nodes["jerusalem.tomb"]["ending"]) != "" and gd.laps_of("jerusalem.tomb") == 2 and gd.laps_of("jerusalem.road") == 2, "the endings take two laps")
	assert_eq(RunData.load_path("stub").laps_of("stub"), 1, "the stub path keeps its single phase")


func test_the_main_run_is_one_lap_everywhere() -> void:
	var d := RunData.load_default()
	assert_eq(d.errors, [])
	for id in d.nodes:
		assert_eq(d.laps_of(str(id)), 1, "%s" % id)
	assert_eq(d.laps_of("no such scene"), 1)


func test_laps_are_validated() -> void:
	var g := RunData.load_path("gospel")
	var nid := "jordan.baptism"
	for bad in [0, 5, -1]:
		g.errors.clear()
		g.nodes[nid]["laps"] = bad
		g._validate_laps(nid, g.nodes[nid])
		assert_false(g.errors.is_empty(), "laps %d is refused" % bad)
	g.errors.clear()
	g.nodes[nid]["laps"] = 4
	g._validate_laps(nid, g.nodes[nid])
	assert_eq(g.errors, [], "four is the most")
	var m := RunData.load_default()
	m.errors.clear()
	m.nodes["warehouse"]["laps"] = 2
	m._validate_laps("warehouse", m.nodes["warehouse"])
	assert_true(str(m.errors).contains("only a path"), "the 174 run keeps its single phase: %s" % str(m.errors))
	m.errors.clear()
	m.nodes["warehouse"]["laps"] = 1
	m.nodes["warehouse"]["arrangement"] = "x"
	m._validate_laps("warehouse", m.nodes["warehouse"])
	assert_eq(m.errors, [])
	g.errors.clear()
	g.nodes[nid]["laps"] = 2
	g.nodes[nid]["arrangement"] = "some"
	g._validate_laps(nid, g.nodes[nid])
	assert_true(str(g.errors).contains("arrangement"), "sections are one lap long: %s" % str(g.errors))


func test_a_path_laps_default_and_a_scenes_own_laps_come_from_the_data_files() -> void:
	var run: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/paths/stub/run.json"))
	(run["path"] as Dictionary)["laps"] = 3
	(run["nodes"][1] as Dictionary)["laps"] = 1
	var p := "user://test_laps_stub_run.json"
	var f := FileAccess.open(p, FileAccess.WRITE)
	f.store_string(JSON.stringify(run))
	f.close()
	var d := RunData.load_files(p, "res://content/paths/stub/music.json", RunData.PACKS_DIR, -1, "res://content/paths/stub/arrangements", "res://content/paths/stub/hotspots")
	assert_eq(d.errors, [], "a path with laps 3 validates")
	assert_eq(d.laps_of(str(run["nodes"][0]["id"])), 3, "the path's laps are the default of every scene")
	assert_eq(d.laps_of(str(run["nodes"][1]["id"])), 1, "a scene's own laps win")
	(run["path"] as Dictionary)["laps"] = 9
	f = FileAccess.open(p, FileAccess.WRITE)
	f.store_string(JSON.stringify(run))
	f.close()
	var d2 := RunData.load_files(p, "res://content/paths/stub/music.json", RunData.PACKS_DIR, -1, "res://content/paths/stub/arrangements", "res://content/paths/stub/hotspots")
	assert_false(d2.errors.is_empty(), "laps 9 is refused")
	DirAccess.remove_absolute(p)


func test_cast_beats_run_across_the_laps_and_not_beyond() -> void:
	var d := RunData.load_path("gospel")
	var id := "jordan.baptism"
	var who := str(d.nodes[id]["cast"][0]["actor"])
	var errs: Array = []
	d.validate_cast_lines(d.nodes[id], [{"actor": who, "at_beat": 127, "act": "nod"}], "t", errs)
	assert_eq(errs, [], "beat 127 is the last beat of two laps")
	d.validate_cast_lines(d.nodes[id], [{"actor": who, "at_beat": 64, "act": "nod"}], "t", errs)
	assert_eq(errs, [], "and beat 64 is the second lap's downbeat")
	d.validate_cast_lines(d.nodes[id], [{"actor": who, "at_beat": 128, "act": "nod"}], "t", errs)
	assert_false(errs.is_empty(), "beat 128 is outside the scene")
	var one := "jordan"
	var who1 := str(d.nodes[one]["cast"][0]["actor"])
	var e1: Array = []
	d.validate_cast_lines(d.nodes[one], [{"actor": who1, "at_beat": 64, "act": "nod"}], "t", e1)
	assert_false(e1.is_empty(), "a one-lap scene still ends at beat 63")
	# a block_fx entry may name its lap
	d.errors.clear()
	d.nodes[id]["block_fx"] = [{"block": 0, "lap": 3, "pass": {}}]
	d._validate_stage_fx(id, d.nodes[id], d.errors)
	assert_true(str(d.errors).contains("lap"), "a block_fx lap beyond the scene's laps is refused: %s" % str(d.errors))
	d.errors.clear()
	d.nodes[id]["block_fx"] = [{"block": 0, "lap": 2, "pass": {}}]
	d._validate_stage_fx(id, d.nodes[id], d.errors)
	assert_eq(d.errors, [])
	# every shipped cast line is inside its laps and nothing spans the gap before the last block
	for pid in SINGLE:
		var pd := RunData.load_path(str(pid))
		for nid in pd.nodes:
			var laps := pd.laps_of(str(nid))
			for ln in pd.nodes[nid].get("cast", []):
				var b := float((ln as Dictionary)["at_beat"])
				assert_true(b >= 0.0 and b <= 64.0 * laps - 1.0, "%s %s: beat %s is inside the scene's %d lap(s)" % [pid, nid, str(b), laps])
				if laps == 2:
					assert_false(b > 95.0 and b < 112.0, "%s %s: beat %s is a stretched story beat or a last-block beat" % [pid, nid, str(b)])


# --- the engine ------------------------------------------------------------------------------------------------------------------

func test_a_two_lap_scene_has_one_window_and_one_commit_at_the_end_of_the_last_lap() -> void:
	var d := RunData.load_path("gospel")
	var e := _engine(d, "jordan.baptism")
	var log := _play(e)
	var bt := e.beat_s
	var starts := _of(log, "phase_start")
	assert_eq(starts.map(func(ev: Dictionary) -> String: return str(ev["node"])), ["jordan.baptism", "jordan.nazareth"], "two scenes started: the second is the next scene, not a second lap")
	var s0: Dictionary = starts[0]
	assert_eq(int(s0["lap"]), 1)
	assert_eq(int(s0["laps"]), 2)
	var laps := _of(log, "lap_start")
	assert_eq(laps.size(), 1)
	assert_eq(int(laps[0]["lap"]), 2)
	assert_eq(int(laps[0]["phase"]), 2, "every lap is a phase of its own")
	assert_near(float(laps[0]["t"]), 64.0 * bt, 1e-9, "the second lap begins on the downbeat 64 beats on")
	assert_near(float(laps[0]["scene_t0"]), 0.0, 1e-12)
	assert_eq(int(starts[1]["phase"]), 3, "the next scene is phase 3")
	assert_eq(int(starts[1]["lap_extra"]), 1, "and counts one lap beyond the one-per-scene")
	assert_near(float(starts[1]["t"]), 128.0 * bt, 1e-9, "after exactly 128 beats")
	assert_eq(e.scene_index(), 2)
	var windows := _of(log, "route_window")
	assert_eq(windows.size(), 1, "one route window in the whole scene")
	assert_near(float(windows[0]["t"]), (64.0 + 48.0) * bt, 1e-9, "at beat 48 of the last lap")
	assert_eq(int(windows[0]["lap"]), 2)
	var commits := _of(log, "route_commit")
	assert_eq(commits.size(), 1)
	assert_near(float(commits[0]["t"]), 128.0 * bt, 1e-9, "the commit is the end of the last lap")
	for hc in _of(log, "hotspot_commit"):
		assert_eq(int(hc["phase"]), 2, "a hotspot commits in the last lap only")
		assert_near(float(hc["t"]), (64.0 + 60.5) * bt, 1e-9, "at the decision of its last block")
	var results := _of(log, "block_result")
	assert_eq(results.size(), 8, "eight blocks are judged")
	assert_eq(results.map(func(r: Dictionary) -> int: return int(r["lap"])), [1, 1, 1, 1, 2, 2, 2, 2])
	assert_eq(results.map(func(r: Dictionary) -> int: return int(r["stage"])), [0, 1, 2, 3, 3, 3, 3, 3], "perfect play: the stage steps on and then stays at the strongest")
	var scene_mixes := _of(log, "mix").filter(func(m: Dictionary) -> bool: return float(m["t"]) < 128.0 * bt - 1e-9)
	assert_eq(scene_mixes.map(func(m: Dictionary) -> int: return int(m["stage"])), [0, 1, 2, 3, 3, 3, 3], "the mix steps up to the strongest and is then only re-affirmed at each block (as ever), never lowered")
	assert_false(scene_mixes.any(func(m: Dictionary) -> bool: return absf(float(m["t"]) - 64.0 * bt) < 1e-9), "and no mix event falls on the lap boundary: nothing changes there")
	assert_eq(_of(log, "reveal").size(), 1, "the bass is revealed once")
	assert_eq(_of(log, "cues").filter(func(c: Dictionary) -> bool: return int(c["phase"]) in [1, 2]).map(func(c: Dictionary) -> String: return str(c["family"])), ["drums", "bass", "drums", "bass", "bass", "bass", "bass", "bass"], "drums, bass, drums, bass, then the bass held")


func test_nothing_can_be_chosen_in_a_lap_before_the_last() -> void:
	var d := RunData.load_path("gospel")
	var e := _engine(d, "jordan.baptism")
	var seen := {"closed": 0, "open": 0}
	_play(e, 2, [], 1.0 / 30.0, func(en: RunEngine, t: float) -> void:
		var beat := en.phase_beat_at(t)
		if en.lap == 1 and beat > 49.0 and beat < 62.0:
			assert_false(en.window_open, "no route window in lap 1")
			assert_false(en.choose(en.default_route()), "and no route can be chosen")
			assert_true(en.hotspots.shown(en.block, en.window_open).is_empty(), "nor a hotspot touched")
			seen["closed"] += 1
		if en.lap == 2 and beat > 50.0 and beat < 60.0:
			assert_true(en.window_open, "the window is open in lap 2")
			assert_true(en.hotspots.shown(en.block, en.window_open).size() >= 2, "with its two to four hotspots on show")
			seen["open"] += 1)
	assert_true(int(seen["closed"]) > 100 and int(seen["open"]) > 100, "both were sampled (%d, %d)" % [int(seen["closed"]), int(seen["open"])])


func test_the_bass_phrase_and_the_grid_go_on_across_the_lap_boundary() -> void:
	for pid_scene in [["gospel", "jordan.baptism"], ["squadron", "air"], ["ember", "north"]]:
		var d := RunData.load_path(str(pid_scene[0]))
		var e := _engine(d, str(pid_scene[1]))
		var log := _play(e, 2)
		var node: Dictionary = d.nodes[str(pid_scene[1])]
		var pack: Dictionary = d.packs[str(node["chart"])]
		var phrase := float(pack["phrase_beats"])
		var tier := str(d.tier_of(int(node["depth"])))
		var starts := {}
		for c in pack["tiers"][tier]["bass"]:
			starts[snappedf(fposmod(float(c[0]) / 960.0, phrase), 0.001)] = true
		var reveal := float((_of(log, "reveal")[0] as Dictionary)["t"]) / e.beat_s
		var lap2_bass := 0
		for n in e.level.notes:
			if str(n["voice"]) != "bass":
				continue
			var gbeat := float(n["tick"]) / 960.0
			assert_true(starts.has(snappedf(fposmod(gbeat - reveal, phrase), 0.001)), "%s: the bass cue at beat %s is a cue of the loop's phrase, counted from the reveal" % [pid_scene[1], str(gbeat)])
			if int(n["phase"]) == 2:
				lap2_bass += 1
		assert_true(lap2_bass > 0, "%s: the second lap has bass cues (%d)" % [pid_scene[1], lap2_bass])
		for n in e.level.notes:  # every cue of both laps is on the grid of the path's tempo: a sixteenth of the 60/bpm beat from the scene's downbeat
			assert_near(float(n["time"]), float(n["tick"]) * 60.0 / (float(d.cfg["timing"]["bpm"]) * 960.0), 1e-9, "%s: cue on the tick grid" % pid_scene[1])


func test_a_missed_block_never_takes_the_bass_out_and_a_late_reveal_may_come_in_the_second_lap() -> void:
	var d := RunData.load_path("gospel")
	# 1. perfect to the end of the first lap, the last block of it missed: the stage holds, the bass stays at its strongest
	var e := _engine(d, "jordan.baptism")
	var log := _play(e, 2, [[1, 3]])
	var lap: Dictionary = _of(log, "lap_start")[0]
	assert_eq(int(lap["stage"]), 3, "a miss holds the stage: lap 2 begins with the bass strongest")
	assert_true(_stages_never_lowered(_of(log, "mix").filter(func(m: Dictionary) -> bool: return float(m["t"]) < 128.0 * e.beat_s - 1e-9)), "no strip-back at the boundary")
	# 2. all of lap 1 missed except the last block: the bass is revealed on the lap's own downbeat
	e = _engine(d, "jordan.baptism")
	log = _play(e, 2, [[1, 0], [1, 1], [1, 2]])
	lap = _of(log, "lap_start")[0]
	assert_eq(int(lap["stage"]), 1, "a pass of the last block steps the stage on into the second lap")
	var rv := _of(log, "reveal")
	assert_eq(rv.size(), 1)
	assert_near(float(rv[0]["t"]), float(lap["t"]), 1e-9, "the bass enters on the second lap's downbeat")
	assert_eq(int(rv[0]["lap"]), 2)
	var fam := _of(log, "cues").filter(func(c: Dictionary) -> bool: return int(c["phase"]) == 2).map(func(c: Dictionary) -> String: return str(c["family"]))
	assert_eq(fam[0], "bass", "its first block is already on the bass cues")
	# 3. everything of lap 1 missed: lap 2 starts again on the drums, and the reveal comes at its own beat 16
	e = _engine(d, "jordan.baptism")
	log = _play(e, 2, [[1, 0], [1, 1], [1, 2], [1, 3]])
	lap = _of(log, "lap_start")[0]
	assert_eq(int(lap["stage"]), 0, "nothing earned: the second lap starts where the first did")
	rv = _of(log, "reveal")
	assert_eq(rv.size(), 1)
	assert_near(float(rv[0]["t"]), float(lap["t"]) + 16.0 * e.beat_s, 1e-9, "and the bass comes in at the second lap's block 2")
	# 4. a perfect first lap and a missed second: the bass is never taken out
	e = _engine(d, "jordan.baptism")
	log = _play(e, 2, [[2, 0], [2, 1], [2, 2]])
	assert_eq(_of(log, "block_result").slice(4).map(func(r: Dictionary) -> int: return int(r["stage"])), [3, 3, 3, 3])
	assert_true(_stages_never_lowered(_of(log, "mix").filter(func(m: Dictionary) -> bool: return float(m["t"]) < 128.0 * e.beat_s - 1e-9)), "the mix is never lowered")


func test_the_energy_rules_are_the_single_phases_block_for_block() -> void:
	var d := RunData.load_path("gospel")
	var cfg: Dictionary = d.cfg
	var pc := float(cfg["judgement"]["pass_credit"])
	var en: Dictionary = cfg["energy"]
	var miss := [[1, 1], [1, 2], [2, 0], [2, 3]]
	var e := _engine(d, "jordan.baptism")
	var log := _play(e, 2, miss)
	var energy := float(en["start"])
	var seen := 0
	for r in _of(log, "block_result"):
		var credit := float(r["credit"])
		if credit >= pc:
			energy += float(en["pass_gain"]) + float(en["pass_bonus"]) * (credit - pc) / maxf(1.0 - pc, 0.001)
		else:
			energy -= float(en["fail_loss"]) * (pc - credit) / pc + 3.0
		energy = clampf(energy, 0.0, float(en["max"]))
		# (a hotspot commit may add its own energy at the last block: compare the block's own change)
		if int(r["lap"]) == 2 and int(r["block"]) == 3:
			break
		assert_near(float(r["energy"]), energy, 1e-9, "phase %d block %d: the single phase's rule" % [int(r["phase"]), int(r["block"])])
		seen += 1
	assert_eq(seen, 7)
	# and the first four blocks of a two-lap scene are those of the same scene at one lap
	var d1 := RunData.load_path("gospel")
	d1.nodes["jordan.baptism"]["laps"] = 1
	var e1 := _engine(d1, "jordan.baptism")
	var l1 := _play(e1, 2, [[1, 1], [1, 2]])
	var r1 := _of(l1, "block_result")
	var r2 := _of(log, "block_result")
	for i in 3:
		assert_near(float(r1[i]["energy"]), float(r2[i]["energy"]), 1e-9, "block %d reads the same at one lap and at two" % i)


func test_cast_lines_count_beats_across_the_laps_and_fire_once_at_any_frame_step() -> void:
	var d := RunData.load_path("gospel")
	var id := "jordan.baptism"
	var lines: Array = d.nodes[id]["cast"]
	var sigs: Array = []
	var fns := {"30": 1.0 / 30.0, "60": 1.0 / 60.0, "odd": 0.0371}
	for k in fns:
		var e := _engine(d, id)
		var log := _play(e, 2, [], float(fns[k]))
		var cs := _of(log, "cast").filter(func(c: Dictionary) -> bool: return str(c["node"]) == id)
		var got := {}
		for c in cs:
			var idx := int(c["index"])
			var ln: Dictionary = lines[idx]
			assert_false(got.has(idx), "line %d fires once" % idx)
			got[idx] = true
			assert_near(float(c["t"]), e.beat_s * float(ln["at_beat"]), 1e-6, "line %d fires on the clock at scene beat %s" % [idx, str(ln["at_beat"])])
			assert_eq(int(c["phase"]), 1 + int(floor(float(ln["at_beat"]) / 64.0)), "and is stamped with the lap it falls in")
			assert_eq(int(c["beat"]), int(ln["at_beat"]))
		for i in lines.size():
			var conditional := false
			for key in ["if_energy_below", "if_energy_above", "if_flags_all", "if_flags_none"]:
				conditional = conditional or (lines[i] as Dictionary).has(key)
			if not conditional:
				assert_true(got.has(i), "line %d (no condition) fired" % i)
		sigs.append(cs.map(func(c: Dictionary) -> String: return "%d|%.5f|%s" % [int(c["index"]), float(c["t"]), str(c["actor"])]))
	assert_eq(sigs[0], sigs[1], "30 and 60 fps agree")
	assert_eq(sigs[0], sigs[2], "and so does an odd step")
	assert_true(lines.any(func(ln: Dictionary) -> bool: return float(ln["at_beat"]) >= 64.0), "the shipped scene has lines in its second lap")


func test_a_stall_across_the_lap_boundary_fires_the_second_laps_lines_after_it_begins() -> void:
	var d := RunData.load_path("stub")
	d.nodes["stub"]["laps"] = 2
	d.nodes["stub"]["cast"] = [{"actor": "x1", "at_beat": 10, "act": "nod"}, {"actor": "x2", "at_beat": 70, "act": "nod"}, {"actor": "x3", "at_beat": 100, "act": "nod"}]
	var e := _engine(d, "stub")
	e.update(-1.0)
	var big := e.update(e.beat_s * 80.0)  # one frame from the start across the whole first lap and 16 beats into the second
	var kinds: Array = big.map(func(ev: Dictionary) -> String: return str(ev["kind"]) if str(ev["kind"]) != "cast" else "cast:" + str(ev["actor"]))
	assert_true(kinds.find("cast:x1") >= 0 and kinds.find("lap_start") > kinds.find("cast:x1"), "the first lap's line, then the lap begins: %s" % str(kinds))
	assert_true(kinds.find("cast:x2") > kinds.find("lap_start"), "the second lap's line comes after the lap began")
	assert_eq(kinds.find("cast:x3"), -1, "and the line at beat 100 is not due")
	var x2: Dictionary = big[kinds.find("cast:x2")]
	assert_near(float(x2["t"]), 70.0 * e.beat_s, 1e-9, "stamped with its own time")
	assert_eq(int(x2["phase"]), 2)


func test_leaving_a_path_in_the_first_lap_ends_the_scene_there() -> void:
	var d := RunData.load_path("gospel")
	var e := _engine(d, "jordan.baptism")
	var st := {"left": false}
	var log := _play(e, 2, [], 1.0 / 30.0, func(en: RunEngine, t: float) -> void:
		if not bool(st["left"]) and en.lap == 1 and en.phase_beat_at(t) >= 61.0:
			assert_false(en.exit_pending(), "nothing is pending before the request")
			st["left"] = en.force_leave()
			assert_true(en.exit_pending(), "the request is pending")
			assert_false(en.window_open))
	assert_true(bool(st["left"]))
	assert_eq(_of(log, "lap_start").size(), 0, "no second lap")
	var ho := _of(log, "path_handoff")
	assert_eq(ho.size(), 1)
	assert_eq(str(ho[0]["route"]), "run:warehouse")
	assert_near(float(ho[0]["t"]), 64.0 * e.beat_s, 1e-9, "on the downbeat that ends the first lap")
	assert_eq(int(ho[0]["lap_extra"]), 0)


func test_the_endings_hand_the_run_back_after_two_laps_on_the_downbeat_and_the_warehouse_grid_is_the_old_one() -> void:
	var gd := RunData.load_path("gospel")
	var main := RunData.load_default()
	var e := _engine(gd, "jerusalem.road")
	var log := _play(e, 3)
	var ho: Dictionary = _of(log, "path_handoff")[0]
	assert_eq(str(ho["route"]), "run:warehouse")
	assert_eq(str(ho["ending"]), "road")
	assert_near(float(ho["t"]), 128.0 * 60.0 / 124.0, 1e-9, "after exactly two laps of the path's tempo")
	assert_eq(int(ho["phase"]), 2)
	assert_eq(int(ho["lap_extra"]), 1)
	assert_true(Session.run_progress != null)
	var me := RunEngine.new(main)
	me.hotspots = RunHotspots.new(main, {}, {})
	me.arrive("warehouse", float(ho["t"]), float(ho["energy"]), int(ho["phase"]), int(ho["lap_extra"]))
	assert_near(me.beat_s, 60.0 / 174.0, 1e-12)
	assert_eq(me.phase_n, 3, "the phase count carries on")
	assert_eq(me.scene_index(), 2, "two scenes so far, two laps beyond")
	var ev := me.update(float(ho["t"]))
	var ps: Dictionary = _of(ev, "phase_start")[0]
	assert_near(float(ps["t"]), float(ho["t"]), 1e-12)
	assert_eq(int(ps["lap_extra"]), 1)
	for n in me.level.notes:
		var x := (float(n["time"]) - float(ho["t"])) / (60.0 / 174.0) * 4.0
		assert_true(absf(x - roundf(x)) < 1e-6, "the Warehouse's cues sit on the 174 grid counted from the handoff downbeat")
	# and into a path from the Warehouse through a portal-like arrive: the path's first scene begins on the downbeat on its own grid
	var pe := RunEngine.new(gd)
	pe.hotspots = RunHotspots.new(gd, {}, {})
	pe.arrive("jordan", 100.0, 70.0, 5, 0)
	pe.update(100.0)
	for n in pe.level.notes:
		var x2 := (float(n["time"]) - 100.0) / (60.0 / 124.0) * 4.0
		assert_true(absf(x2 - roundf(x2)) < 1e-6, "and the path's cues on its own")


func test_the_main_run_has_no_laps() -> void:
	var d := RunData.load_default()
	var e := _engine(d, "warehouse")
	var log := _play(e, 4)
	assert_eq(_of(log, "lap_start").size(), 0)
	for ps in _of(log, "phase_start"):
		assert_eq(int(ps["lap"]), 1)
		assert_eq(int(ps["laps"]), 1)
		assert_eq(int(ps["lap_extra"]), 0)
	assert_eq(e.phase_n, e.scene_index())
	assert_eq(_of(log, "route_window").size(), 3, "one window per phase, as ever")
	assert_eq(_of(log, "block_result").size(), 12)


# --- the audio -------------------------------------------------------------------------------------------------------------------

func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	return a


func test_the_voices_play_on_across_the_lap_boundary_and_the_bass_never_drops() -> void:
	var d := RunData.load_path("gospel")
	var e := _engine(d, "jordan.baptism")
	var log := _play(e, 2)
	var a := _audio(d)
	var bass_targets: Array = []  # [t, target] after every scheduled item that touches the live group
	var group_phase := {}
	for ev in log:
		if str(ev["kind"]) in ["phase_start", "mix", "reveal", "lap_start", "route_window"]:
			if str(ev["kind"]) == "route_window":
				continue  # (the riser and fall are effect players; not under test here)
			a.on_event(ev)
	var n_items: Array = a._schedule.map(func(i: Dictionary) -> String: return str(i["kind"]))
	assert_false(n_items.has("lap"), "the lap boundary schedules nothing")
	assert_eq(n_items.filter(func(k: String) -> bool: return k == "phase").size(), 2, "one phase item for each of the two scenes, none for the lap")
	while not a._schedule.is_empty():
		var item: Dictionary = a._schedule.pop_front()
		a._run(item, 0.0, 0.0)
		var g := a._live_group()
		if not g.is_empty() and g["voices"].has("bass") and str(item["kind"]) == "mix":
			bass_targets.append([float(item["t"]), float(g["voices"]["bass"]["target"])])
		if not g.is_empty() and int(g["phase"]) == 1:
			group_phase[str(item["kind"])] = true
		if str(item["kind"]) == "phase" and int(item["ev"]["phase"]) == 3:
			break
	var scene_voices: Array = a.voice_log.filter(func(v: Dictionary) -> bool: return str(v["node"]) == "jordan.baptism")
	assert_eq(scene_voices.map(func(v: Dictionary) -> String: return str(v["voice"])), ["drums", "bass", "other"], "three voices for the whole scene: nothing started at the lap boundary")
	for v in scene_voices:
		assert_true(float(v["target"]) < 64.0 * e.beat_s - 1e-6 or str(v["voice"]) == "x", "every voice began in the first lap")
	assert_true(bass_targets.size() >= 3)
	var after_reveal := bass_targets.filter(func(x: Array) -> bool: return float(x[0]) >= 16.0 * e.beat_s - 1e-6)
	for x in after_reveal:
		assert_true(float(x[1]) >= 0.85 - 1e-9, "the bass aims at %.2f from beat %.0f on: never lower than the drums-return stage's" % [float(x[1]), float(x[0]) / e.beat_s])
	var live_pairs: Array = a._groups.map(func(g: Dictionary) -> String: return str(g["buses"]))
	assert_eq(live_pairs.size(), 2, "the old scene fades while the new one plays")
	assert_true(live_pairs[0] != live_pairs[1], "and the two scenes use the two bus pairs, as they always did (the extra lap does not shift the pairs)")
	a.queue_free()


# --- the real scene --------------------------------------------------------------------------------------------------------------

func test_the_scene_plays_both_laps_of_a_path_scene_and_shows_the_hotspots_in_both() -> void:  # (N2.1: selection is open for the whole scene; the route window is still the second lap's only)
	var d := _scene({"RW_RUN_PATH": "gospel", "RW_RUN_START": "jordan.baptism", "RW_RUN_TAPS": "scripted"})
	var scene: Node = d["scene"]
	var bt: float = scene.engine.beat_s
	assert_eq(scene.engine.laps, 2)
	_run_until(scene, 55.0 * bt, func() -> bool: return false)
	assert_eq(scene.engine.lap, 1)
	var lap1: Array = scene.hotspot_items()
	assert_true(lap1.size() >= 2 and lap1.size() <= 8, "the choices are on show at beat 55 of the first lap too (%d)" % lap1.size())
	assert_false(scene.engine.window_open, "but the engine's route window is the last lap's")
	_run_until(scene, 62.8 * bt, func() -> bool: return false)
	assert_eq(scene._door_phase, -1, "no door walk is latched in the first lap")
	assert_true(scene._passage_swap < 0.0, "and no frame closes")
	_run_until(scene, 66.0 * bt, func() -> bool: return false)
	assert_eq(scene.engine.lap, 2)
	assert_eq(scene.lap_log.size(), 1)
	assert_eq(int(scene.lap_log[0]["lap"]), 2)
	assert_eq(scene.phase_log.size(), 1, "the scene's own phase log has one entry per scene")
	_run_until(scene, (64.0 + 55.0) * bt, func() -> bool: return false)
	var items: Array = scene.hotspot_items()
	assert_true(items.size() >= 2 and items.size() <= 8, "two to eight hotspots on show in the second lap (%d)" % items.size())
	_run_until(scene, 140.0 * bt, func() -> bool: return scene.phase_log.size() >= 2)
	assert_eq(scene.phase_log.size(), 2)
	assert_eq(scene.engine.scene_index(), 2)
	assert_eq(scene.summary()["nodes"].size(), 2)
	assert_eq(scene.summary()["laps"], ["jordan.baptism"], "one lap_start for the one two-lap scene")
	assert_true(Session.run_progress.path_world_reached("gospel", "jordan"))
	_free(d)


func test_the_pause_menus_leave_works_in_the_first_lap() -> void:
	var d := _scene({"RW_RUN_PATH": "gospel", "RW_RUN_START": "jordan.baptism"})
	var scene: Node = d["scene"]
	var bt: float = scene.engine.beat_s
	_run_until(scene, 20.0 * bt, func() -> bool: return false)
	assert_true(scene.request_path_leave())
	_run_until(scene, 62.6 * bt, func() -> bool: return false)
	assert_true(scene._passage_swap >= 0.0, "the frame closes over the last beats of the first lap")
	_run_until(scene, 80.0 * bt, func() -> bool: return not scene.path_log.is_empty())
	assert_eq(scene.path_log.size(), 1)
	assert_eq(scene.path_log[0]["kind"], "leave")
	assert_near(float(scene.path_log[0]["t"]), 64.0 * bt, 1e-9, "at the end of the first lap, not the second")
	assert_eq(scene.lap_log.size(), 0)
	assert_eq(scene.run_path, "")
	_free(d)


# --- the debug mode ----------------------------------------------------------------------------------------------------------------

func test_the_debug_mode_names_the_lap() -> void:
	var d := RunData.load_path("gospel")
	var info2 := PlaytestCatalog.scene_info(d, "jordan.baptism")
	var info1 := PlaytestCatalog.scene_info(d, "jordan")
	assert_eq(int(info2["laps"]), 2)
	assert_eq(int(info1["laps"]), 1)
	var live := {"phase": 2, "lap": 2, "laps": 2, "scene_beat": 70.0, "scene_beats": 128.0, "block": 1, "stage": 3, "stage_label": "Bass strongest", "cue": "bass", "beat": 6.0, "t": 40.0, "energy": 80.0,
		"section": 1, "sections": 1, "pack": str(info2["audio"]["sections"][0]["pack"]), "chart_pack": str(info2["audio"]["sections"][0]["pack"]), "gains": {}, "stage_gains": {"drums": 0.4, "bass": 1.0, "other": 0.5}, "counting_in": false, "bassment": false}
	var text := "\n".join(PackedStringArray(PlaytestOverlay.lines(info2, live)))
	assert_contains(text, "lap 2 of 2", "the overlay says which lap")
	assert_contains(text, "70.0/128", "and the beat of the scene across both laps")
	var live1 := live.duplicate()
	live1["laps"] = 1
	live1["lap"] = 1
	var text1 := "\n".join(PackedStringArray(PlaytestOverlay.lines(info1, live1)))
	assert_contains(text1, "phase 2", "a one-lap scene reads as before")
	assert_false(text1.contains("lap 1 of"))
	var entry := PlaytestNotes.make_entry(info2, live, "like")
	assert_eq(int(entry["lap"]), 2)
	assert_eq(int(entry["laps"]), 2)
	assert_contains(PlaytestNotes.entry_markdown(entry), "lap 2 of 2", "the notes carry the lap")
	assert_contains(str(PlaytestCatalog.audio_sections(info2)), "2 laps of 64 beats", "the scene's Info says it plays two laps")
	assert_contains(str(PlaytestCatalog.audio_sections(info1)), "phase 64 beats", "and a one-lap scene says as before")
