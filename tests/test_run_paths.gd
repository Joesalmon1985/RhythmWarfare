extends TestCase
## Sister runs (docs/THREE_PATHS_AND_FACES_PLAN.md section 3, stage 2): a path is its own run.json at its own tempo, entered from a Warehouse portal through a TEMPO HANDOFF and left by an ending's
## way back. Pure checks first (the clock's rates, the data and its relaxed graph rules, the tempo of the packs, the portal hotspots, the save), then the engine handoff in both directions
## (beat_s before and after, the phase starting on the downbeat, the cues on the new grid, the energy carried), then the audio clock swap, then the real scene on its virtual clock
## (RW_PATH_REMAP=gospel=stub plays the stub path through the balcony portal; RW_RUN_PATH=stub starts it directly). The matrix once per path is in test_run_matrix.gd.

const TMP := "user://test_run_paths"
const TMP_SAVE := "user://test_run_paths_save.json"
const REMAP := "gospel=stub"

var _saved: RunProgress


func _write(path: String, v: Variant) -> void:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(v, "\t"))
	f.close()


func _read(path: String) -> Dictionary:
	return JSON.parse_string(FileAccess.get_file_as_string(path))


func _remap_on() -> void:
	OS.set_environment("RW_PATH_REMAP", REMAP)


func _remap_off() -> void:
	OS.unset_environment("RW_PATH_REMAP")


# --- the clock's rates ---------------------------------------------------------------------------------------------------------

func test_frames_per_beat_is_a_whole_number_at_every_tempo() -> void:
	var rates := {174: 8700, 124: 8680, 140: 8400, 145: 8700}
	for bpm in [174, 124, 140, 145, 120, 128, 150, 100, 97]:
		var rate := RunAudio.clock_rate(bpm)
		var exact := 60.0 * float(rate) / float(bpm)
		assert_near(exact, roundf(exact), 1e-9, "%d BPM at %d Hz: a beat is %f frames" % [bpm, rate, exact])
		assert_eq(RunAudio.frames_per_beat(bpm), int(roundf(exact)), "%d BPM: frames_per_beat" % bpm)
		assert_true(rate >= 8000, "%d BPM: the rate stays a cheap 8-bit clock (%d Hz)" % [bpm, rate])
		if rates.has(bpm):
			assert_eq(rate, rates[bpm], "%d BPM has the planned rate" % bpm)
		var s := RunAudio.silent_loop(64, bpm)
		assert_eq(s.mix_rate, rate)
		assert_eq(s.loop_end, 64 * RunAudio.frames_per_beat(bpm), "%d BPM: the 64-beat loop is a whole number of frames" % bpm)
		assert_eq(s.data.size(), s.loop_end)
		assert_near(s.get_length(), 64.0 * 60.0 / float(bpm), 1e-9, "%d BPM: no rounding in the grid the song clock reads" % bpm)
	assert_eq(RunAudio.frames_per_beat(124), 4200)
	assert_eq(RunAudio.frames_per_beat(140), 3600)
	assert_eq(RunAudio.frames_per_beat(145), 3600)
	assert_eq(RunAudio.frames_per_beat(174), 3000)


# --- the data and its relaxed rules ------------------------------------------------------------------------------------------

func test_the_stub_path_loads_and_the_main_run_does_not_see_its_packs() -> void:
	var d := RunData.load_path("stub")
	assert_eq(d.errors, [], "the stub path validates")
	assert_true(d.is_path())
	assert_eq(d.path_id, "stub")
	assert_eq(int(d.cfg["timing"]["bpm"]), 124)
	assert_eq((d.cfg["stages"] as Array).size(), 4, "the sections a path leaves out are the main run's")
	assert_eq(d.node_order, ["stub", "stub.end"])
	assert_eq(d.start_node(), "stub")
	assert_eq(d.nodes["stub.end"]["ending"], "done")
	assert_eq(d.nodes["stub.end"]["next"][0]["to"], "run:warehouse")
	for id in d.packs:
		assert_eq(str(d.packs[id].get("path", "")), "stub", "only the path's own packs are loaded: %s" % id)
		assert_eq(int(d.packs[id]["bpm"]), 124)
	assert_true(d.packs.has("stub_start") and d.packs.has("stub_end"))
	assert_true(d.nodes["stub"]["temporary"], "placeholder music is marked temporary")
	var main := RunData.load_default()
	assert_eq(main.errors, [], "the main run still validates with the path's packs on disk")
	assert_false(main.is_path())
	assert_false(main.packs.has("stub_start"), "the 174 run never loads a path's pack")
	assert_eq(int(main.cfg["timing"]["bpm"]), 174)


func _stub_files(tag: String, mutate: Callable) -> RunData:
	var run := _read("res://content/paths/stub/run.json")
	var music := _read("res://content/paths/stub/music.json")
	mutate.call(run, music)
	var dir := TMP + "/" + tag
	_write(dir + "/run.json", run)
	_write(dir + "/music.json", music)
	return RunData.load_files(dir + "/run.json", dir + "/music.json", RunData.PACKS_DIR, 1, dir + "/arrangements", dir + "/hotspots")


func _errors_have(d: RunData, needle: String) -> bool:
	for e in d.errors:
		if str(e).contains(needle):
			return true
	return false


func test_a_path_may_have_several_entries_exits_and_endings_the_main_run_may_not() -> void:
	var add_second := func(run: Dictionary, music: Dictionary) -> void:
		var alt: Dictionary = (run["nodes"][0] as Dictionary).duplicate(true)
		alt["id"] = "stub.alt"
		alt["scene"] = "alt"
		alt["title"] = "The Other Door"
		alt["entry"] = true  # a second entry scene of the same world
		alt["exit_scene"] = false
		alt["ending"] = "other"  # and a second ending
		alt["next"] = [{"to": "run:warehouse", "dir": "up", "label": "Back"}]
		run["nodes"].append(alt)
		(run["nodes"][0]["next"] as Array).append({"to": "stub.alt", "dir": "right", "label": "The other door"})
		run["nodes"][0]["place"]["rail"]["exits"]["right"] = "to_bar"
		music["nodes"].append({"id": "stub.alt", "audio": "stub_start", "chart": "stub_start", "treatment": "none", "temporary": true})
	var d := _stub_files("two_entries", add_second)
	assert_eq(d.errors, [], "a path world with two entries, two endings and a scene reached from the first: valid")
	assert_eq(d.entry_of("stub"), "stub", "the world's own id stays its first entry")
	# the same data as a main run (no `path` block) is refused: one entry scene and one exit scene per world, no run: route
	var as_main := func(run: Dictionary, music: Dictionary) -> void:
		add_second.call(run, music)
		run.erase("path")
	var m := _stub_files("as_main", as_main)
	assert_true(_errors_have(m, "exactly one entry scene"), "the main run keeps one entry per world: %s" % str(m.errors))
	assert_true(_errors_have(m, "only for an ending scene of a path"), "and the way back is for paths only")


func test_a_path_without_an_ending_or_with_a_dead_end_is_refused() -> void:
	var no_ending := func(run: Dictionary, _music: Dictionary) -> void:
		for n in run["nodes"]:
			(n as Dictionary).erase("ending")
		run["nodes"][1]["next"] = [{"to": "stub", "dir": "up", "label": "Round again", "loop": true}]
	var d := _stub_files("no_ending", no_ending)
	assert_true(_errors_have(d, "no ending scene"), str(d.errors))
	assert_true(_errors_have(d, "cannot reach an ending"), str(d.errors))
	var bad_return := func(run: Dictionary, _music: Dictionary) -> void:
		run["path"]["returns_to"] = "mothership"
	var d2 := _stub_files("bad_return", bad_return)
	assert_true(_errors_have(d2, "returns_to"), str(d2.errors))
	var not_entry := func(run: Dictionary, _music: Dictionary) -> void:
		run["nodes"][0]["entry"] = false
	var d3 := _stub_files("not_entry", not_entry)
	assert_true(_errors_have(d3, "entry"), str(d3.errors))


func test_a_pack_at_the_wrong_tempo_for_its_path_is_refused() -> void:
	# a packs folder with the stub's two packs, one of them re-tagged at 174 BPM (pack.json only: the loader validates, it does not play)
	var packs := TMP + "/packs"
	for id in ["stub_start", "stub_end"]:
		var p := _read("res://songs/packs/%s/pack.json" % id)
		if id == "stub_end":
			p["bpm"] = 174
		_write("%s/%s/pack.json" % [packs, id], p)
	var dir := "res://content/paths/stub"
	var d := RunData.load_files(dir + "/run.json", dir + "/music.json", packs, 1, dir + "/arrangements", dir + "/hotspots")
	assert_true(_errors_have(d, "pack stub_end is 174 BPM, the run is 124"), str(d.errors))
	assert_false(_errors_have(d, "pack stub_start"), "and only the wrong one")
	# a 124 BPM pack handed to the main run (no path tag) is refused too
	var odd := _read("res://songs/packs/stub_start/pack.json")
	odd.erase("path")
	odd["id"] = "odd_house"
	_write(TMP + "/packs_main/odd_house/pack.json", odd)
	for id in ["lv1_warehouse"]:
		_write("%s/packs_main/%s/pack.json" % [TMP, id], _read("res://songs/packs/%s/pack.json" % id))
	var m := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, TMP + "/packs_main", 1, RunData.ARRANGEMENTS_DIR, RunData.HOTSPOTS_DIR)
	assert_true(_errors_have(m, "pack odd_house is 124 BPM, the run is 174"), "the 174 run refuses a 124 BPM pack")


func test_a_music_json_that_misses_a_scene_or_points_at_a_missing_pack_is_refused() -> void:
	var gone := func(_run: Dictionary, music: Dictionary) -> void:
		music["nodes"] = [music["nodes"][0]]
	var d := _stub_files("music_gone", gone)
	assert_true(_errors_have(d, "no entry for node stub.end"), str(d.errors))
	var other_path := func(_run: Dictionary, music: Dictionary) -> void:
		music["nodes"][1]["audio"] = "lv1_warehouse"  # a main-run pack at 174 BPM: not loaded for the path
		music["nodes"][1]["chart"] = "lv1_warehouse"
	var d2 := _stub_files("music_main_pack", other_path)
	assert_true(_errors_have(d2, "pack 'lv1_warehouse' does not exist"), str(d2.errors))


# --- the portals ---------------------------------------------------------------------------------------------------------------

func test_portal_hotspots_follow_the_rules_and_stay_out_of_play_until_their_path_exists() -> void:
	_remap_off()
	var d := RunData.load_default()
	assert_eq(d.errors, [])
	var missing: Array = ["gospel", "squadron", "ember"].filter(func(p: String) -> bool: return not RunData.path_exists(p))
	assert_eq(d.skipped_portals.size(), missing.size(), "a path that is not written yet has its portal left out (and logged)")
	var star_in := false
	for h in d.hotspots_of("warehouse.balcony"):
		star_in = star_in or str(h["id"]) == "warehouse.balcony.star"
	assert_eq(star_in, RunData.path_exists("gospel"), "the star is in play exactly when the gospel path exists")
	_remap_on()
	var r := RunData.load_default()
	assert_eq(r.errors, [])
	var skipped: Array = r.skipped_portals.map(func(s: Dictionary) -> String: return str(s["hotspot"]))
	skipped.sort()
	var want_skipped: Array = []
	if not RunData.path_exists("ember"):
		want_skipped.append("warehouse.bar.ember")
	if not RunData.path_exists("squadron"):
		want_skipped.append("warehouse.booth.radio")
	assert_eq(skipped, want_skipped, "the gospel portal plays once its path (here the stub) exists")
	var star: Dictionary = {}
	for h in r.hotspots_of("warehouse.balcony"):
		if str(h["id"]) == "warehouse.balcony.star":
			star = h
	assert_false(star.is_empty(), "the star is in the balcony's hotspots")
	assert_eq(star["kind"], "secret")
	assert_eq(star["look"]["available"], "pulse")
	assert_false(star["default"], "never the default")
	assert_true(star["repeatable"])
	assert_eq(star["on_success"]["route"], "path:gospel")
	assert_eq(star["on_failure"].get("route", ""), "", "a failure keeps the scene's default route")
	assert_true(float(star["on_failure"]["energy"]) < 0.0)
	assert_eq(float(star["on_failure"]["energy"]), -4.0)
	_remap_off()
	# the three portals as authored, whatever exists: kind, look and place in the 2 to 4 rule
	var raw: Dictionary = _read("res://content/run/hotspots/warehouse.json")
	var found := {}
	for h in raw["hotspots"]:
		if str(h["on_success"].get("route", "")).begins_with("path:"):
			found[str(h["id"])] = str(h["on_success"]["route"])
			assert_eq(h["kind"], "secret")
			assert_eq(h["look"]["available"], "pulse")
			assert_false(h["default"])
	assert_eq(found, {"warehouse.balcony.star": "path:gospel", "warehouse.booth.radio": "path:squadron", "warehouse.bar.ember": "path:ember"})
	for route in ["path:gospel", "path:ember", "path:x_1"]:
		assert_true(HotspotContract.is_path_route(route))
	assert_false(HotspotContract.is_path_route("path:"))
	assert_false(HotspotContract.is_path_route("trial:1"))
	assert_true(HotspotContract.is_run_route("run:warehouse"))
	assert_eq(HotspotContract.path_of("path:squadron"), "squadron")


## Plan D10 (visual polish): once a path has been finished (any of its endings' keep: flags), its Warehouse portal shows a look of its own; the data says which flags and which look.
func test_a_finished_path_gives_its_portal_a_look_of_its_own() -> void:
	var raw: Dictionary = _read("res://content/run/hotspots/warehouse.json")
	var seen := 0
	for h in raw["hotspots"]:
		var route := str(h["on_success"].get("route", ""))
		if not route.begins_with("path:"):
			continue
		var pid := route.trim_prefix("path:")
		var fin: Dictionary = h["look"].get("finished", {})
		assert_false(fin.is_empty(), "%s has a finished look" % h["id"])
		var want: Array = []
		var pd := RunData.load_path(pid)
		for sid in pd.nodes:
			if str(pd.nodes[sid].get("ending", "")) != "":
				want.append("keep:path_%s_%s" % [pid, pd.nodes[sid]["ending"]])
		want.sort()
		var got: Array = (fin["flags_any"] as Array).duplicate()
		got.sort()
		assert_eq(got, want, "%s: its flags are exactly its path's endings" % h["id"])
		assert_true(str(fin["available"]) in HotspotContract.LOOK_FINISHED, "a look of its own, not the pulse")
		var held := {}
		var has := func(f: String) -> bool: return held.has(f)
		var hn := HotspotContract.normalize(h.duplicate(true), "warehouse", "night_one")
		assert_false(HotspotContract.finished_look(hn, has), "%s: the plain pulse before any ending" % h["id"])
		held[want[0]] = true
		assert_true(HotspotContract.finished_look(hn, has), "%s: the finished look once an ending is kept" % h["id"])
		seen += 1
	assert_eq(seen, 3, "the three portals")
	assert_eq(RunData.load_default().errors, [], "the main run validates with the finished looks")
	var errors: Array = []
	HotspotContract._validate_finished({"flags_any": ["path_gospel_tomb"]}, "t", errors)
	assert_eq(errors.size(), 1, "a finished look reads keep: flags only (they outlive the run)")
	errors = []
	HotspotContract._validate_finished({"flags_any": ["keep:path_gospel_tomb"], "available": "sparkle"}, "t", errors)
	assert_eq(errors.size(), 1, "an unknown finished look is refused")
	errors = []
	HotspotContract._validate_finished({"flags_any": []}, "t", errors)
	assert_eq(errors.size(), 1, "no flags, no finished look")


func test_the_portal_resolves_both_ways_through_the_hotspot_engine() -> void:
	_remap_on()
	var d := RunData.load_default()
	var flags := {"wh_saw_floor": true}
	var hs := RunHotspots.new(d, flags, {})
	hs.begin_scene("warehouse.balcony", 60.0)
	assert_true(hs.is_shown("warehouse.balcony.star", 3, true), "the star shows once the floor has been seen")
	assert_false(RunHotspots.new(d, {}, {}).is_shown("warehouse.balcony.star", 3, true), "and not before")
	assert_true(hs.select("warehouse.balcony.star", 3, true))
	var ok := hs.commit_final(true)
	assert_eq(ok["route"], "path:gospel")
	assert_true(bool(ok["success"]))
	hs.begin_scene("warehouse.balcony", 60.0)
	assert_true(hs.is_shown("warehouse.balcony.star", 3, true), "repeatable: it is not spent by a success")
	hs.select("warehouse.balcony.star", 3, true)
	var bad := hs.commit_final(false)
	assert_eq(bad["route"], "warehouse.chill", "a failure flickers out and the scene's default exit takes over")
	assert_true(bool(bad["continued"]))
	assert_eq(float(bad["energy"]), -4.0)
	# nothing tapped: the default exit whatever happens
	hs.begin_scene("warehouse.balcony", 60.0)
	assert_eq(hs.commit_final(true)["route"], "warehouse.chill")
	_remap_off()


# --- the save -----------------------------------------------------------------------------------------------------------------

func _rm(path: String) -> void:
	if FileAccess.file_exists(path):
		DirAccess.remove_absolute(path)


func test_the_save_gains_paths_and_an_old_save_is_migrated() -> void:
	_rm(TMP_SAVE)
	_write(TMP_SAVE, {"version": 2, "reached": {"warehouse": {"entries": 3}, "mothership": {"entries": 1}}, "runs": 4, "best_phases": 9, "migrated_from": "", "flags": {"keep:x": true}, "seed": 7})
	var p := RunProgress.load_data(TMP_SAVE, "user://none.json")
	assert_false(p.recovered_from_corrupt, "an old save is read, not set aside")
	assert_eq(p.paths, {}, "the paths are added on load")
	assert_eq(int(p.data["version"]), 2, "the version stays 2")
	assert_true(p.is_reached("mothership") and p.flags.has("keep:x"), "nothing else changes")
	assert_true(p.path_enter("stub", "stub"), "a new path world is new")
	assert_false(p.path_enter("stub", "stub"), "and then it is not")
	assert_true(p.path_ending("stub", "done"))
	assert_false(p.path_ending("stub", "done"))
	assert_true(p.path_world_reached("stub", "stub"))
	assert_eq(p.path_endings("stub"), ["done"])
	assert_false(p.reached_ids().has("stub"), "a path's worlds never enter the main run's reached levels")
	var q := RunProgress.load_data(TMP_SAVE, "user://none.json")
	assert_eq(q.paths, {"stub": {"reached": ["stub"], "endings": ["done"]}}, "and it round-trips")
	assert_eq(int(q.data["version"]), 2)
	# a fresh save and the chapter migration carry the key too
	_rm(TMP_SAVE)
	var f := RunProgress.load_data(TMP_SAVE, "user://none.json")
	assert_eq(f.paths, {})
	_rm(TMP_SAVE)


# --- the engine handoff, both ways ---------------------------------------------------------------------------------------------

## Plays `e` with perfect hits until it hands off (a path_handoff event) or `max_s` of song time have gone. `select` is a hotspot id touched at beat 52 of every phase ("" none); with `miss_last` the last
## block of every phase is not played. Returns {events, t, handoff}.
func _play(e: RunEngine, t0: float, select := "", miss_last := false, max_s := 400.0, leave_beat := -1.0) -> Dictionary:
	var events: Array = []
	var next_i := 0
	var down: Dictionary = {}
	var t := t0 - 0.5
	var selected_phase := -1
	var handoff: Dictionary = {}
	while t < t0 + max_s and handoff.is_empty():
		for ev in e.update(t):
			events.append(ev)
			if str(ev["kind"]) == "path_handoff":
				handoff = ev
		while next_i < e.level.notes.size() and float(e.level.notes[next_i]["time"]) <= t + 0.2:
			var n: Dictionary = e.level.notes[next_i]
			if not (miss_last and int(n["block"]) == 3):
				down[next_i] = float(n["time"])
			next_i += 1
		for i in down.keys():
			var n2: Dictionary = e.level.notes[i]
			var st: Variant = down[i]
			if typeof(st) == TYPE_FLOAT and float(st) <= t:
				e.press(int(n2["pad"]), float(st), int(n2["pad"]))
				down[i] = {"up": float(n2["end_time"]) if n2["type"] == "hold" else float(st) + 0.06}
			elif typeof(st) == TYPE_DICTIONARY and float((st as Dictionary)["up"]) <= t:
				e.release(int(n2["pad"]), float((st as Dictionary)["up"]), int(n2["pad"]))
				down.erase(i)
		if leave_beat >= 0.0 and e.window_open and e.phase_beat_at(t) >= leave_beat:
			e.force_leave()
		if select != "" and e.window_open and selected_phase != e.phase_n and e.phase_beat_at(t) > 52.0:
			selected_phase = e.phase_n
			e.hotspots.select(select, e.block, e.window_open)
		t += 1.0 / 30.0
	return {"events": events, "t": t, "handoff": handoff}


func _kinds(events: Array, kind: String) -> Array:
	return events.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == kind)


func _on_grid(e: RunEngine, from_note: int, origin: float) -> bool:
	for i in range(from_note, e.level.notes.size()):
		var x := (float(e.level.notes[i]["time"]) - origin) / e.beat_s * 4.0  # every stub cue is on a sixteenth of the engine's own beat
		if absf(x - roundf(x)) > 1e-6:
			return false
	return true


func test_the_portal_hands_the_run_to_the_path_on_the_downbeat_and_back_again() -> void:
	_remap_on()
	var main := RunData.load_default()
	var flags := {"wh_saw_floor": true}
	var e := RunEngine.new(main)
	e.hotspots = RunHotspots.new(main, flags, {})
	e.begin("warehouse.balcony")
	var beat174 := 60.0 / 174.0
	assert_near(e.beat_s, beat174, 1e-12)
	var r := _play(e, 0.0, "warehouse.balcony.star")
	var ho: Dictionary = r["handoff"]
	assert_false(ho.is_empty(), "the committed portal ends the phase by a handoff")
	assert_eq(ho["route"], "path:gospel")
	assert_eq(ho["target"], "gospel")
	assert_eq(ho["from"], "warehouse.balcony")
	assert_near(float(ho["t"]), e.t_of(64.0), 1e-9, "on the downbeat")
	assert_near(float(ho["t"]), 64.0 * beat174, 1e-9, "after exactly one 64-beat phase of the 174 grid")
	assert_eq(e.away, "path:gospel")
	assert_eq(_kinds(r["events"], "phase_start").size(), 1, "the Warehouse engine started no second phase")
	assert_true(e.update(float(ho["t"]) + 30.0).is_empty(), "a handed-off engine is frozen")
	assert_true(float(ho["energy"]) > 0.0)
	assert_eq(int(ho["phase"]), 1)
	# the path's engine arrives on that downbeat
	var pd := RunData.load_path("gospel")
	assert_eq(pd.path_id, "stub")
	var pe := RunEngine.new(pd)
	pe.hotspots = RunHotspots.new(pd, flags, {})
	pe.arrive(pd.start_node(), float(ho["t"]), float(ho["energy"]), int(ho["phase"]))
	var beat124 := 60.0 / 124.0
	assert_near(pe.beat_s, beat124, 1e-12, "beat_s after the handoff")
	assert_true(absf(pe.beat_s - e.beat_s) > 0.1, "and it differs from before (%f / %f)" % [e.beat_s, pe.beat_s])
	assert_near(pe.grid_origin, float(ho["t"]), 1e-12)
	assert_near(pe.level.bpm, 124.0, 1e-12)
	var evs := pe.update(float(ho["t"]))
	var ps: Dictionary = _kinds(evs, "phase_start")[0]
	assert_near(float(ps["t"]), float(ho["t"]), 1e-12, "the path's phase starts on the downbeat")
	assert_eq(ps["node"], "stub")
	assert_eq(int(ps["phase"]), 2, "the phase count carries on")
	assert_eq(ps["path"], "stub")
	var mix: Dictionary = _kinds(evs, "mix")[0]
	assert_eq(int(mix["stage"]), 0, "on drums alone")
	assert_eq(float(mix["gains"]["bass"]), 0.0)
	assert_near(pe.energy, float(ho["energy"]), 1e-9, "the crowd's energy carries across")
	assert_near(pe.t_of(64.0), float(ho["t"]) + 64.0 * beat124, 1e-9, "a phase is 64 beats of the new tempo")
	assert_true(pe.level.notes.size() > 0)
	assert_eq(pe.cue_family(0), "drums")
	assert_true(float(pe.level.notes[0]["time"]) >= float(ho["t"]) - 1e-9, "no cue before the downbeat")
	assert_true(_on_grid(pe, 0, float(ho["t"])), "every cue of the first block is on the new grid (sixteenths of 60/124 s from the downbeat)")
	for n in pe.level.notes:
		assert_true(float(n["time"]) - float(ho["t"]) < 12.1 * beat124 + 0.001, "the first block's cues lie in its first 12 beats of the new tempo")
	# play the path to its ending: the default exits, nothing tapped
	var r2 := _play(pe, float(ho["t"]))
	var back: Dictionary = r2["handoff"]
	assert_false(back.is_empty(), "the ending hands the run back")
	assert_eq(back["route"], "run:warehouse")
	assert_eq(back["target"], "warehouse")
	assert_eq(back["ending"], "done")
	assert_eq(back["from"], "stub.end")
	assert_near(float(back["t"]), float(ho["t"]) + 2.0 * 64.0 * beat124, 1e-9, "two phases of the path")
	assert_eq(_kinds(r2["events"], "phase_start").map(func(ev: Dictionary) -> String: return str(ev["node"])), ["stub.end"], "stub, then its ending")
	var flagged := false
	for ev in _kinds(r2["events"], "hotspot_commit"):
		flagged = flagged or (ev["outcome"]["flags_set"] as Array).has("keep:path_stub_done")
	assert_true(flagged, "the ending's way back sets keep:path_stub_done")
	# the way back: the Warehouse engine begins again on the new downbeat, its beat the old one
	var me := RunEngine.new(main)
	me.hotspots = RunHotspots.new(main, flags, {})
	me.arrive("warehouse", float(back["t"]), float(back["energy"]), int(back["phase"]))
	assert_near(me.beat_s, beat174, 1e-12, "beat_s after the return")
	var ev2 := me.update(float(back["t"]))
	var ps2: Dictionary = _kinds(ev2, "phase_start")[0]
	assert_near(float(ps2["t"]), float(back["t"]), 1e-12)
	assert_eq(ps2["node"], "warehouse")
	assert_eq(int(ps2["phase"]), int(back["phase"]) + 1)
	assert_near(me.energy, float(back["energy"]), 1e-9, "energy carries back")
	assert_true(_on_grid174(me, float(back["t"])), "the Warehouse's cues sit on the 174 grid again, counted from the new downbeat")
	_remap_off()


func _on_grid174(e: RunEngine, origin: float) -> bool:
	for n in e.level.notes:
		var x := (float(n["time"]) - origin) / (60.0 / 174.0) * 4.0
		if absf(x - roundf(x)) > 1e-6:
			return false
	return true


func test_a_failed_portal_flickers_out_and_the_warehouse_goes_on() -> void:
	_remap_on()
	var main := RunData.load_default()
	var e := RunEngine.new(main)
	e.hotspots = RunHotspots.new(main, {"wh_saw_floor": true}, {})
	e.begin("warehouse.balcony")
	var r := _play(e, 0.0, "warehouse.balcony.star", true, 24.0)
	assert_true(r["handoff"].is_empty(), "no handoff when the last block is missed")
	var commits := _kinds(r["events"], "hotspot_commit")
	assert_eq(commits.size(), 1)
	var out: Dictionary = commits[0]["outcome"]
	assert_false(bool(out["success"]))
	assert_eq(out["hotspot"], "warehouse.balcony.star")
	assert_eq(out["route"], "warehouse.chill", "the default route")
	assert_eq(float(out["energy"]), -4.0)
	assert_eq(e.away, "")
	assert_eq(e.node_id, "warehouse.chill", "the Warehouse goes on")
	_remap_off()


func test_the_pause_menus_leave_is_the_ways_back_taken_at_the_end_of_the_phase() -> void:
	var pd := RunData.load_path("stub")
	var e := RunEngine.new(pd)
	e.hotspots = RunHotspots.new(pd, {}, {})
	e.begin("stub")
	assert_true(e.force_leave(), "allowed inside a path")
	e.choice = ""
	var main := RunData.load_default()
	var m := RunEngine.new(main)
	m.begin("warehouse")
	assert_false(m.force_leave(), "and not in the main run")
	var r := _play(e, 0.0, "", false, 400.0, 61.0)  # asked for at beat 61, after the hotspots have committed
	var h: Dictionary = r["handoff"]
	assert_eq(h["route"], "run:warehouse")
	assert_eq(h["from"], "stub", "left from the first scene, not an ending")
	assert_eq(h["ending"], "", "and no ending is recorded")
	assert_near(float(h["t"]), 64.0 * 60.0 / 124.0, 1e-9)


# --- the audio clock ----------------------------------------------------------------------------------------------------------

func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	return a


func test_the_clock_swap_is_one_scheduled_item_before_the_phase_that_starts_on_it() -> void:
	var main := RunData.load_default()
	var pd := RunData.load_path("stub")
	var a := _audio(main)
	assert_near(a.beat_s, 60.0 / 174.0, 1e-12)
	assert_eq(a.player.stream.mix_rate, 8700)
	assert_near(a.loop_seconds, 64.0 * 60.0 / 174.0, 1e-9)
	var t := 64.0 * 60.0 / 174.0
	a.schedule_clock_swap(pd, t)
	assert_near(a.beat_s, 60.0 / 124.0, 1e-12, "new events are scheduled on the new beat at once")
	assert_near(a.loop_seconds, 64.0 * 60.0 / 174.0, 1e-9, "the old loop's length is kept until the swap runs (its last wrap is at this downbeat)")
	a.on_event({"kind": "phase_start", "node": "stub", "t": t, "phase": 2, "treatment": "none", "audio": "stub_start", "temporary": true, "fresh": false, "world": "stub"})
	assert_eq(a._schedule.map(func(i: Dictionary) -> String: return str(i["kind"])), ["clock", "phase"], "the clock goes first, in the order they were added")
	var item: Dictionary = a._schedule[0]
	a._run(item, t + 0.004, 0.003)
	assert_eq(a.clock_log.size(), 1)
	var c: Dictionary = a.clock_log[0]
	assert_eq(int(c["bpm"]), 124)
	assert_eq(int(c["frames_per_beat"]), 4200)
	assert_eq(int(c["rate"]), 8680)
	assert_near(float(c["from"]), 0.007, 1e-9, "it starts as far in as the call is late")
	assert_eq(a.player.stream.mix_rate, 8680)
	# The song time stays ONE unbroken line across the swap (the Stage 3 follow-up, docs/paths/gospel.md): a stream's position reads as of the END of the last mixed chunk and the new stream's first chunk
	# starts at `from`, so after its first mix it reads from + one mix period; the base is lowered by that period, which makes song_base + from + period = now + the time to the next mix, the old
	# line's value at that mix. (Before the fix the base was the downbeat itself: the clock ran one mix period ahead from the swap on, 88.5 ms with the dummy driver.)
	var period := float(c["period"])
	assert_true(period >= 0.003 and period <= 0.25, "a mix period (%f)" % period)
	assert_near(a.song_base, t - period, 1e-12, "the base is the downbeat less one mix period")
	assert_near(a.song_base + float(c["from"]) + period, (t + 0.004) + 0.003, 1e-9, "the new line meets the old one at the next mix")
	assert_near(a.loop_seconds, 64.0 * 60.0 / 124.0, 1e-9)
	assert_eq(a._wraps, 0)
	# and back
	a.schedule_clock_swap(main, t + a.loop_seconds)
	a._run(a._schedule[a._schedule.size() - 1], t + a.loop_seconds, 0.0)
	assert_eq(a.player.stream.mix_rate, 8700)
	assert_near(a.loop_seconds, 64.0 * 60.0 / 174.0, 1e-9)
	assert_near(a.beat_s, 60.0 / 174.0, 1e-12)
	a.queue_free()


# --- the real scene on its virtual clock ---------------------------------------------------------------------------------------------

func _isolate_save() -> void:
	_saved = Session.run_progress
	_rm(TMP_SAVE)
	Session.run_progress = RunProgress.load_data(TMP_SAVE, "user://none.json")


func _restore_save() -> void:
	if _saved != null:
		Session.run_progress = _saved
		_saved = null
	_rm(TMP_SAVE)


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
	for k in ["RW_RUN_VIRTUAL", "RW_RUN_BOT", "RW_RUN_ROUTES", "RW_PATH_REMAP", "RW_RUN_FLAGS", "RW_RUN_PORTAL", "RW_RUN_START", "RW_RUN_PATH", "RW_RUN_PATH_START"]:
		OS.unset_environment(k)


func _run_until(scene: Node, t_end: float, stop: Callable) -> void:
	var t: float = scene._vt
	while t < t_end and not stop.call():
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)


func test_the_scene_enters_the_stub_path_through_the_balcony_portal_and_leaves_by_its_ending() -> void:
	var d := _scene({"RW_PATH_REMAP": REMAP, "RW_RUN_FLAGS": "wh_saw_floor", "RW_RUN_PORTAL": "warehouse.balcony.star", "RW_RUN_START": "warehouse.balcony", "RW_RUN_TAPS": "scripted"})
	var scene: Node = d["scene"]
	assert_eq(scene.run_path, "", "the run begins in the Warehouse")
	var proxy_before: Object = scene.proxy.level
	var energy_at_handoff := -1.0
	_run_until(scene, 40.0, func() -> bool: return not scene.path_log.is_empty())
	assert_eq(scene.path_log.size(), 1, "the portal was entered")
	var enter: Dictionary = scene.path_log[0]
	assert_eq(enter["kind"], "enter")
	assert_eq(enter["path"], "stub")
	assert_near(float(enter["beat_s_before"]), 60.0 / 174.0, 1e-12)
	assert_near(float(enter["beat_s_after"]), 60.0 / 124.0, 1e-12)
	assert_near(float(enter["t"]), 64.0 * 60.0 / 174.0, 1e-9, "on the downbeat that ends the Warehouse phase")
	assert_eq(scene.run_path, "stub")
	assert_true(scene.data.is_path())
	assert_eq(scene.engine.node_id, "stub")
	assert_near(scene.engine.beat_s, 60.0 / 124.0, 1e-12, "the engine the pads and the judge read is the path's")
	assert_true(scene.pad_view.level == scene.engine.level, "the pads show the path's cues")
	assert_true(scene.hud.engine == scene.engine, "the HUD follows")
	assert_true(scene.proxy.level == scene.engine.level and scene.proxy.level != proxy_before, "the stages read the new level")
	for w in scene.stages:
		assert_near((scene.stages[w]["stage"] as StoryStage).bpm, 124.0, 1e-9, "stage %s takes the new tempo" % w)
	assert_true(scene.hotspots.data == scene.data, "the hotspots are the path's")
	assert_near(scene.engine.phase_t0, float(enter["t"]), 1e-12, "the path's first phase starts on the downbeat")
	assert_eq(scene.engine.phase_n, 2)
	assert_true(Session.run_progress.path_world_reached("stub", "stub"), "the path's world is saved as reached")
	assert_false(Session.run_progress.reached_ids().has("stub"), "and the main run's levels are untouched")
	energy_at_handoff = scene.engine.energy
	# on through the stub to its ending and back
	_run_until(scene, 200.0, func() -> bool: return scene.path_log.size() >= 2)
	assert_eq(scene.path_log.size(), 2)
	var leave: Dictionary = scene.path_log[1]
	assert_eq(leave["kind"], "leave")
	assert_eq(leave["ending"], "done")
	assert_near(float(leave["beat_s_before"]), 60.0 / 124.0, 1e-12)
	assert_near(float(leave["beat_s_after"]), 60.0 / 174.0, 1e-12)
	assert_near(float(leave["t"]), float(enter["t"]) + 2.0 * 64.0 * 60.0 / 124.0, 1e-9)
	assert_eq(scene.run_path, "")
	assert_false(scene.data.is_path())
	assert_eq(scene.engine.node_id, "warehouse", "back on the Warehouse floor")
	assert_near(scene.engine.beat_s, 60.0 / 174.0, 1e-12)
	assert_true(scene.engine.energy > 0.0 and energy_at_handoff > 0.0)
	assert_eq(Session.run_progress.path_endings("stub"), ["done"], "the ending is saved")
	assert_true(Session.run_progress.flags.has("keep:path_stub_done"), "and so is its flag")
	for w in scene.stages:
		assert_near((scene.stages[w]["stage"] as StoryStage).bpm, 174.0, 1e-9)
	var worlds: Array = scene.phase_log.map(func(p: Dictionary) -> String: return "%s:%s" % [p["path"], p["node"]])
	assert_eq(worlds.slice(0, 4), [":warehouse.balcony", "stub:stub", "stub:stub.end", ":warehouse"], "the phases in order: %s" % str(worlds))
	# the run goes on in the Warehouse for a phase after the return (the hotspots are the Warehouse's again)
	_run_until(scene, scene._vt + 30.0, func() -> bool: return scene.phase_log.size() >= 5)
	assert_true(scene.phase_log.size() >= 5, "and the Warehouse's own route goes on")
	_free(d)


func test_the_scene_starts_in_a_path_and_the_pause_menu_leaves_it() -> void:
	var d := _scene({"RW_RUN_PATH": "stub"})
	var scene: Node = d["scene"]
	assert_eq(scene.run_path, "stub")
	assert_eq(scene.engine.node_id, "stub")
	assert_eq(scene.engine.phase_n, 1)
	assert_near(scene.engine.beat_s, 60.0 / 124.0, 1e-12)
	assert_true(scene.main_data == null, "the Warehouse's data is loaded only when the path is left")
	_run_until(scene, 20.0, func() -> bool: return false)
	assert_true(scene.request_path_leave())
	_run_until(scene, 80.0, func() -> bool: return not scene.path_log.is_empty())
	assert_eq(scene.path_log.size(), 1)
	assert_eq(scene.path_log[0]["kind"], "leave")
	assert_eq(scene.path_log[0]["ending"], "", "left from the first room by the menu: no ending")
	assert_near(float(scene.path_log[0]["t"]), 64.0 * 60.0 / 124.0, 1e-9, "at the end of the phase it was asked in")
	assert_eq(scene.run_path, "")
	assert_eq(scene.engine.node_id, "warehouse")
	assert_near(scene.engine.beat_s, 60.0 / 174.0, 1e-12)
	assert_true(scene.main_data != null and scene.main_data == scene.data)
	assert_eq(Session.run_progress.path_endings("stub"), [], "no ending was reached")
	_free(d)


func test_a_portal_into_a_path_that_does_not_exist_yet_is_not_on_show() -> void:
	var d := _scene({"RW_RUN_FLAGS": "wh_saw_floor", "RW_RUN_START": "warehouse.balcony"})
	var scene: Node = d["scene"]
	_run_until(scene, 52.0 * 60.0 / 174.0, func() -> bool: return false)
	var ids: Array = scene.hotspots.shown(scene.engine.block, scene.engine.window_open).map(func(h: Dictionary) -> String: return str(h["id"]))
	assert_eq(ids.has("warehouse.balcony.star"), RunData.path_exists("gospel"), "a portal is on show exactly when its path has data (%s)" % str(ids))
	assert_true(ids.size() >= 2 and ids.size() <= 4)
	_free(d)


func test_a_window_opens_with_the_audio_on_even_at_an_ending_and_a_portals_start_pack_is_loaded_ahead() -> void:
	var d := _scene({"RW_RUN_PATH": "stub", "RW_RUN_START": "stub.end"})
	var scene: Node = d["scene"]
	var a := RunAudio.new()
	scene.add_child(a)
	a.configure(scene.data)
	scene.audio = a
	scene._open_routes({"options": scene.engine.options(), "effect": "riser", "t": 0.0})
	assert_true(a._requested.is_empty(), "an ending's way back is no scene: nothing to preload")
	scene._open_routes({"options": [{"to": "stub"}], "effect": "fall", "t": 0.0})
	assert_true(a._requested.size() >= 3, "a real next scene's three stems are requested (%d)" % a._requested.size())
	scene.audio = null
	a.queue_free()
	_free(d)
	_remap_on()
	var main := RunData.load_default()
	var au := RunAudio.new()
	tree.root.add_child(au)
	au.configure(main)
	var pd := RunData.load_path("stub")
	au.preload_pack("stub_start", pd)
	var stem := "res://songs/packs/stub_start/loops/drums.wav"
	assert_true(au._requested.has(stem) or ResourceLoader.has_cached(stem), "a pack of another run's data is loaded ahead from that data (requested, or already cached)")
	au.preload_pack("stub_start")  # without the other data the main run's own packs are searched: a pack it does not have is ignored (no error)
	au.queue_free()
	_remap_off()
