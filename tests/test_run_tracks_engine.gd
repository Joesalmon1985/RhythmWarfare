extends TestCase
## Track scenes in the engine (docs/RUN_TRACK_SCENES.md "Behaviour"), on the virtual clock with synthetic packs and no audio: the track's tempo inside the run's phase structure, laps with open
## doors (leave early, stay, the default at the end, the touch on the final lap, a failed last block on an early leave), the hotspots reset between laps, cues from the chart, neutral blocks, the tempo
## changing between scenes (and across a path hand-off) with exact beat times on both sides, a minigame's hold past the plan with the wrap, the energy numbers of track scenes.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")
const B174 := 60.0 / 174.0


# --- helpers ---------------------------------------------------------------------------------------------------------------------

func _engine(d: RunData, start: String) -> RunEngine:
	assert_eq(d.errors, [], "the run data (with its track scenes) validates")
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin(start)
	return e


## Plays from song time `t0` with a scripted player who hits every cue on time except those `miss(note)` names, until `stop(e)` is true (or the run ends / hands off / `max_s` passes). `at(e, t)` is
## called every frame (taps, holds). Returns every event.
func _play(e: RunEngine, stop: Callable, miss: Callable = Callable(), at: Callable = Callable(), t0 := -0.5, max_s := 3000.0) -> Array:
	var log: Array = []
	var next_i := 0
	var down := {}
	var t := t0
	while t < t0 + max_s and not e.over and e.away == "" and not bool(stop.call(e)):
		if at.is_valid():
			at.call(e, t)
		log.append_array(e.update(t))
		while next_i < e.level.notes.size() and float(e.level.notes[next_i]["time"]) <= t + 0.5:
			if not (miss.is_valid() and bool(miss.call(e.level.notes[next_i]))):
				down[next_i] = float(e.level.notes[next_i]["time"])
			next_i += 1
		for i in down.keys():
			var n: Dictionary = e.level.notes[i]
			var st: Variant = down[i]
			if typeof(st) == TYPE_FLOAT and float(st) <= t:
				e.press(int(n["pad"]), float(st), int(n["pad"]))
				down[i] = {"up": float(n["end_time"]) if n["type"] == "hold" else float(st) + 0.06}
			elif typeof(st) == TYPE_DICTIONARY and float((st as Dictionary)["up"]) <= t:
				e.release(int(n["pad"]), float((st as Dictionary)["up"]), int(n["pad"]))
				down.erase(i)
		t += 1.0 / 30.0
	return log


func _of(log: Array, kind: String) -> Array:
	return log.filter(func(ev: Dictionary) -> bool: return str(ev["kind"]) == kind)


func _scene_is(n: int) -> Callable:
	return func(e: RunEngine) -> bool: return e.scene_index() >= n


## Every cue of phases [p0, p1] sits on the 174 grid counted from `origin` (sixteenths).
func _on_grid(e: RunEngine, p0: int, p1: int, origin: float, beat: float) -> bool:
	var any := false
	for n in e.level.notes:
		if int(n["phase"]) < p0 or int(n["phase"]) > p1:
			continue
		any = true
		var x := (float(n["time"]) - origin) / beat * 4.0
		if absf(x - roundf(x)) > 1e-6:
			return false
	return any


func _go_back(extra := {}) -> Dictionary:
	var spec := Fx.go_back_spec()
	spec.merge(extra, true)
	return spec


# --- a whole track scene ------------------------------------------------------------------------------------------------------------

func test_a_track_scene_plays_its_laps_at_the_tracks_tempo_and_takes_the_default_exit_at_the_end() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var plan := d.track_scenes.plan_of("warehouse")
	assert_eq(int(plan["laps"]), 4)
	var e := _engine(d, "warehouse")
	var beat := 60.0 / 174.0032
	assert_near(e.beat_s, beat, 1e-12, "the scene runs at the track's tempo")
	assert_near(e.level.bpm, 174.0032, 1e-9)
	assert_true(e.is_track_scene())
	var lap_s := 64.0 * beat
	var log := _play(e, _scene_is(2))
	var ps := _of(log, "phase_start")
	assert_eq(ps.size(), 2)
	assert_eq(str(ps[0]["track"]), "acuna_go_back", "phase_start names the track")
	assert_eq(int(ps[0]["laps"]), 4)
	var ts := _of(log, "track_start")
	assert_eq(ts.size(), 1)
	assert_near(float(ts[0]["t"]), 0.0, 1e-12)
	assert_eq(int(ts[0]["entry_bar"]), 40)
	assert_near(float(ts[0]["track_t"]), 0.0013 + 160.0 * beat, 1e-9)
	assert_eq(int(ts[0]["laps"]), 4)
	assert_eq(int(ts[0]["doors_from_lap"]), 2)
	assert_near(float(ts[0]["bpm"]), 174.0032, 1e-9)
	assert_eq(str(ts[0]["dir"]), Fx.root().path_join("acuna_go_back"))
	var tempos := _of(log, "tempo")
	assert_eq(tempos.size(), 2, "the tempo changes at the track scene's first downbeat and back at the next scene's")
	assert_near(float(tempos[0]["bpm"]), 174.0032, 1e-9)
	assert_near(float(tempos[1]["t"]), 4.0 * lap_s, 1e-9)
	assert_near(float(tempos[1]["bpm"]), 174.0, 1e-9)
	var laps := _of(log, "lap_start")
	assert_eq(laps.map(func(x: Dictionary) -> int: return int(x["lap"])), [2, 3, 4], "lap_start fires as for a path scene's laps")
	var tl := _of(log, "track_lap")
	assert_eq(tl.size(), 3)
	for k in tl.size():
		assert_near(float(tl[k]["t"]), float(k + 1) * lap_s, 1e-9, "lap %d starts %d x 64 beats in" % [k + 2, k + 1])
		assert_near(float(tl[k]["track_t"]), float(plan["entry_t"]) + float(k + 1) * lap_s, 1e-9, "the track goes on without a break")
		assert_true(bool(tl[k]["doors_open"]))
	var win := _of(log, "route_window")
	assert_eq(win.map(func(x: Dictionary) -> int: return int(x["lap"])), [2, 3, 4], "no window in lap 1; a window in every later lap")
	assert_eq(win.map(func(x: Dictionary) -> bool: return bool(x["last"])), [false, false, true])
	for w in win:
		assert_near(float(w["t"]), (float(w["lap"]) - 1.0) * lap_s + 48.0 * beat, 1e-9, "at the third block's boundary of its lap")
	assert_eq(_of(log, "track_last_lap"), [], "nothing touched: no lap became the last early")
	var hc := _of(log, "hotspot_commit")
	assert_eq(hc.size(), 1, "one commit, at the end of the plan's final lap")
	assert_true(bool(hc[0]["outcome"]["defaulted"]), "the default exit")
	assert_near(float(hc[0]["t"]), 3.0 * lap_s + 60.5 * beat, 1e-9, "at the final lap's choice beat")
	var rc := _of(log, "route_commit")
	assert_eq(rc.size(), 1)
	assert_eq(str(rc[0]["to"]), "warehouse.bar")
	assert_near(float(rc[0]["t"]), 4.0 * lap_s, 1e-9, "the scene lasts four laps")
	var te := _of(log, "track_end")
	assert_eq(te.size(), 1)
	assert_near(float(te[0]["t"]), 4.0 * lap_s, 1e-9)
	assert_near(float(te[0]["track_t"]), float(plan["end_t"]), 1e-9, "the track has reached bar 104")
	assert_eq(str(te[0]["reason"]), "route")
	var br := _of(log, "block_result").filter(func(x: Dictionary) -> bool: return str(x["node"]) == "warehouse")
	assert_eq(br.size(), 16, "16 blocks in four laps")
	for x in br:
		assert_true(bool(x["passed"]))
		assert_near(float(x["t"]), (float(x["lap"]) - 1.0) * lap_s + (16.0 * float(x["block"]) + 12.5) * beat, 1e-9, "judged at beat 12.5 of its block, the track's beat")
	# the next scene is an ordinary one at 174 BPM on its own downbeat
	assert_eq(e.node_id, "warehouse.bar")
	assert_false(e.is_track_scene())
	assert_near(e.beat_s, B174, 1e-12)
	assert_near(e.level.bpm, 174.0, 1e-12)
	assert_near(e.phase_t0, 4.0 * lap_s, 1e-9)
	assert_true(_on_grid(e, 5, 5, 4.0 * lap_s, B174), "the next scene's cues sit on the 174 grid counted from its downbeat")
	var ticks: Array = e.level.notes.map(func(n: Dictionary) -> int: return int(n["tick"]))
	var sorted := ticks.duplicate()
	sorted.sort()
	assert_eq(ticks, sorted, "ticks keep growing across the tempo change")
	Fx.clear()


func test_touching_an_exit_on_lap_2_makes_it_the_last_lap() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var e := _engine(Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}}), "warehouse")
	var beat := e.beat_s
	var lap_s := 64.0 * beat
	var touched := [false]
	var at := func(en: RunEngine, t: float) -> void:
		if not touched[0] and en.lap == 2 and en.window_open and en.phase_beat_at(t) > 50.0:
			touched[0] = en.hotspots.select("warehouse.exit_balcony", en.block, en.window_open)
	var refused := [true]
	var at1 := func(en: RunEngine, t: float) -> void:
		if en.lap == 1 and en.phase_beat_at(t) > 50.0 and en.phase_beat_at(t) < 51.0:
			refused[0] = refused[0] and not en.choose("warehouse.balcony") and not en.window_open
		at.call(en, t)
	var log := _play(e, _scene_is(2), Callable(), at1)
	assert_true(refused[0], "lap 1: no window, nothing can be chosen")
	assert_true(touched[0], "the exit could be touched in lap 2's window")
	var last := _of(log, "track_last_lap")
	assert_eq(last.size(), 1)
	assert_eq(int(last[0]["lap"]), 2)
	assert_near(float(last[0]["t"]), lap_s + 60.5 * beat, 1e-9, "decided at lap 2's choice beat")
	assert_near(float(last[0]["ends_t"]), 2.0 * lap_s, 1e-9)
	assert_eq(str(last[0]["route"]), "warehouse.balcony")
	var hc := _of(log, "hotspot_commit")
	assert_eq(hc.size(), 1)
	assert_eq(str(hc[0]["outcome"]["hotspot"]), "warehouse.exit_balcony")
	assert_true(bool(hc[0]["outcome"]["success"]))
	var rc := _of(log, "route_commit")
	assert_eq(str(rc[0]["to"]), "warehouse.balcony")
	assert_near(float(rc[0]["t"]), 2.0 * lap_s, 1e-9, "the scene ends after lap 2 (44 s)")
	assert_eq(_of(log, "lap_start").size(), 1, "no lap 3")
	var te := _of(log, "track_end")
	assert_near(float(te[0]["t"]), 2.0 * lap_s, 1e-9)
	assert_eq(e.node_id, "warehouse.balcony")
	Fx.clear()


func test_touching_an_exit_on_the_final_lap_is_the_usual_last_lap() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var e := _engine(Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back", "laps": 3}}}), "warehouse")
	var lap_s := 64.0 * e.beat_s
	var at := func(en: RunEngine, t: float) -> void:
		if en.lap == 3 and en.window_open and en.hotspots.selected == "" and en.phase_beat_at(t) > 50.0 and en.phase_beat_at(t) < 51.0:
			en.hotspots.select("warehouse.exit_balcony", en.block, en.window_open)
	var log := _play(e, _scene_is(2), Callable(), at)
	assert_eq(_of(log, "track_last_lap"), [], "the final lap is the last already")
	assert_eq(_of(log, "route_commit")[0]["to"], "warehouse.balcony")
	assert_near(float(_of(log, "route_commit")[0]["t"]), 3.0 * lap_s, 1e-9)
	assert_eq(_of(log, "route_window").size(), 2, "windows in laps 2 and 3")
	assert_eq(_of(log, "hotspot_commit").size(), 1)
	Fx.clear()


## A copy of the run's hotspot files where the Warehouse's balcony exit, failed, leads to the bar (the shipped one fails into the balcony too).
func _hotspots_with_a_failure_route() -> String:
	var dir := ProjectSettings.globalize_path("user://test_track_hotspots")
	DirAccess.make_dir_recursive_absolute(dir)
	var src := DirAccess.open(RunData.HOTSPOTS_DIR)
	for f in src.get_files():
		if f.get_extension() != "json":
			continue
		var text := FileAccess.get_file_as_string(RunData.HOTSPOTS_DIR.path_join(f))
		if f == "warehouse.json":
			var v: Dictionary = JSON.parse_string(text)
			for h in v["hotspots"]:
				if str(h["id"]) == "warehouse.exit_balcony":
					h["on_failure"]["route"] = "warehouse.bar"
			text = JSON.stringify(v, " ")
		var fa := FileAccess.open(dir.path_join(f), FileAccess.WRITE)
		fa.store_string(text)
		fa.close()
	return dir


func test_a_failed_last_block_on_an_early_leave_follows_the_exits_failure_route() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7, RunData.ARRANGEMENTS_DIR, _hotspots_with_a_failure_route())
	RunTrackScenes.load_for(d, Fx.write_scenes({"main": {"warehouse": {"track": "acuna_go_back"}}}), Fx.root())
	var e := _engine(d, "warehouse")
	var lap_s := 64.0 * e.beat_s
	var at := func(en: RunEngine, t: float) -> void:
		if en.lap == 2 and en.window_open and en.hotspots.selected == "" and en.phase_beat_at(t) > 50.0 and en.phase_beat_at(t) < 51.0:
			en.hotspots.select("warehouse.exit_balcony", en.block, en.window_open)
	var miss := func(n: Dictionary) -> bool: return int(n["phase"]) == 2 and int(n["block"]) == 3
	var log := _play(e, _scene_is(2), miss, at)
	var hc := _of(log, "hotspot_commit")
	assert_eq(hc.size(), 1)
	assert_false(bool(hc[0]["outcome"]["success"]), "the missed last block fails the touched exit")
	assert_eq(str(_of(log, "track_last_lap")[0]["route"]), "warehouse.bar")
	assert_eq(str(_of(log, "route_commit")[0]["to"]), "warehouse.bar", "its failure route")
	assert_near(float(_of(log, "route_commit")[0]["t"]), 2.0 * lap_s, 1e-9, "at the end of lap 2")
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://test_track_hotspots"))
	Fx.clear()


func test_the_hotspots_reset_between_laps_and_the_card_table_keeps_its_rule() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"ward": {"track": "acuna_go_back"}}})
	var card := ""
	for h in d.hotspots_of("ward"):
		if RunHotspots.window_of(h) == "any":
			card = str(h["id"])
	assert_true(card != "", "the ward has the card table")
	var e := _engine(d, "ward")
	var state := {"sel2": false, "lap3_sel": "x", "lap1": false}
	var at := func(en: RunEngine, t: float) -> void:
		var pb := en.phase_beat_at(t)
		if en.lap == 1 and not state["lap1"] and pb > 2.0:  # the card table may be touched in any block of any lap: here in lap 1's first block
			state["lap1"] = en.hotspots.select(card, en.block, en.window_open)
		if en.lap == 2 and not state["sel2"] and en.block == 3 and pb > 50.0:  # touched after the third block's decision: its commit would be lap 3's first decision
			state["sel2"] = en.hotspots.select(card, en.block, en.window_open)
		if en.lap == 3 and str(state["lap3_sel"]) == "x":
			state["lap3_sel"] = en.hotspots.selected
	var log := _play(e, func(en: RunEngine) -> bool: return en.lap >= 3 and en.block >= 1, Callable(), at)
	assert_true(bool(state["lap1"]))
	var hc := _of(log, "hotspot_commit")
	assert_eq(hc.size(), 1, "the card table touched in lap 1 commits at that block's decision, and nothing else commits")
	assert_eq(int(hc[0]["phase"]), 1)
	assert_eq(int(hc[0]["block"]), 0)
	assert_true(bool(state["sel2"]), "the card table could be touched in lap 2's last block")
	assert_eq(str(state["lap3_sel"]), "", "the next lap starts with nothing selected (the touch state reset)")
	assert_eq(_of(log, "track_last_lap"), [], "a touch that does not lead out of the scene does not end it")
	Fx.clear()


# --- cues ---------------------------------------------------------------------------------------------------------------------

func test_the_cues_come_from_the_chart_moved_to_scene_time_and_cut_to_the_run_rhythm() -> void:
	Fx.clear()
	# 150 BPM, drop1 at bar 56: entry bar 40 = track beat 160 is scene beat 0. Extras by track beat: a tap at block beat 11.5 (kept) and 12.5 (left out), a hold of 6 beats from block beat 8
	# (cut to 4), a 2-beat hold from block beat 11.75 (a quarter beat left: a tap), a 2-beat hold that fits; the bass is the focus from bar 48 (scene beat 32).
	var extra := [{"beat": 171.5, "pad": 1}, {"beat": 172.5, "pad": 3}, {"beat": 184.0, "pad": 2, "dur_beats": 6.0}, {"beat": 203.75, "pad": 4, "dur_beats": 2.0}, {"beat": 210.0, "pad": 1, "dur_beats": 2.0}]
	Fx.write_pack("cue_pack", {"bpm": 150.0, "bars": 200, "cue_bars": [36, 120], "bass_from_bar": 48, "extra": extra, "sections": [["intro", "intro", 0, 56], ["d1", "drop", 56, 120]]})
	var d := Fx.main_data({"main": {"warehouse": {"track": "cue_pack"}}})
	var plan := d.track_scenes.plan_of("warehouse")
	assert_eq(int(plan["entry_bar"]), 40)
	var e := _engine(d, "warehouse")
	var beat := 60.0 / 150.0
	var log := _play(e, _scene_is(2))
	var entry_t := float(plan["entry_t"])
	var lap_s := 64.0 * beat
	var scene: Array = e.level.notes.filter(func(n: Dictionary) -> bool: return int(n["phase"]) <= int(plan["laps"]))
	assert_true(scene.size() > 100)
	for n: Dictionary in scene:
		var lap_k := int(n["lap"])
		assert_eq(lap_k, int(n["phase"]), "a cue's lap is its phase here (the first scene)")
		var scene_beat := (float(n["time"])) / beat
		var in_lap := scene_beat - float(lap_k - 1) * 64.0
		var blk := int(floor(in_lap / 16.0 + 1e-9))
		assert_eq(blk, int(n["block"]), "the cue's block is the block its time falls in")
		var in_block := in_lap - 16.0 * float(blk)
		assert_true(in_block >= -1e-6 and in_block <= 12.0 + 1e-6, "in the block's first 12 beats (%f)" % in_block)
		assert_near(float(n["time"]), float(n["track_t"]) - entry_t, 1e-9, "scene time = track time minus the entry bar's time")
		assert_true(float(n["track_t"]) >= entry_t - 1e-9 and float(n["track_t"]) < float(plan["end_t"]), "nothing from outside the scene")
		if n["type"] == "hold":
			assert_true(in_block + (float(n["end_time"]) - float(n["time"])) / beat <= 12.0 + 1e-6, "a hold ends by beat 12")
		var voice := str(n["voice"])
		assert_true(voice in ["drums", "bass"], "the pack's voice is kept")
		if voice == "drums":
			assert_eq(str(n["family"]), "kick" if int(n["pad"]) <= 2 else "snare")
		else:
			assert_eq(str(n["family"]), "bass")
		assert_near(float(n["tick"]) / 960.0, scene_beat, 1e-3, "the tick counts the run's beats")
	var at := func(b: float) -> Array: return scene.filter(func(n: Dictionary) -> bool: return absf(float(n["time"]) / beat - b) < 1e-6)
	assert_eq(at.call(11.5).size(), 1, "the tap at beat 11.5 is kept")
	assert_eq(at.call(12.5).size(), 0, "the tap at beat 12.5 (the rest) is left out")
	var h1: Array = at.call(24.0)
	assert_eq(h1.size(), 1)
	assert_eq(str(h1[0]["type"]), "hold")
	assert_near((float(h1[0]["end_time"]) - float(h1[0]["time"])) / beat, 4.0, 1e-9, "the 6-beat hold from block beat 8 is cut to end at beat 12")
	assert_eq(int(h1[0]["duration_ticks"]), 4 * 960)
	var h2: Array = at.call(43.75)
	assert_eq(h2.size(), 1)
	assert_eq(str(h2[0]["type"]), "tap", "a hold left shorter than half a beat becomes a tap")
	assert_eq(int(h2[0]["duration_ticks"]), 0)
	assert_eq(str(h2[0]["voice"]), "bass")
	assert_eq(str(h2[0]["family"]), "bass")
	var h3: Array = at.call(50.0)
	assert_eq(str(h3[0]["type"]), "hold")
	assert_near((float(h3[0]["end_time"]) - float(h3[0]["time"])) / beat, 2.0, 1e-9, "a hold that ends by beat 12 is kept whole")
	var cues_ev := _of(log, "cues").filter(func(x: Dictionary) -> bool: return x.has("track"))
	assert_eq(cues_ev.size(), 4 * int(plan["laps"]), "one cues event per block of the scene")
	assert_eq(str(cues_ev[0]["family"]), "track")
	# later laps repeat nothing: each lap reads its own 16 bars
	var lap2: Array = scene.filter(func(n: Dictionary) -> bool: return int(n["lap"]) == 2)
	assert_near(float(lap2[0]["track_t"]) - entry_t, float(lap2[0]["time"]), 1e-9)
	assert_true(float(lap2[0]["time"]) >= lap_s - 1e-9)
	Fx.clear()


func test_a_block_without_cues_is_neutral() -> void:
	Fx.clear()
	Fx.write_pack("gap_pack", {"bpm": 160.0, "bars": 200, "cue_bars": [36, 120], "gap_bars": [[44, 48]], "sections": [["intro", "intro", 0, 56], ["d1", "drop", 56, 120]]})
	var e := _engine(Fx.main_data({"main": {"warehouse": {"track": "gap_pack"}}}), "warehouse")
	var log := _play(e, func(en: RunEngine) -> bool: return en.lap >= 2)
	var br := _of(log, "block_result")
	assert_eq(br.size(), 4)
	assert_false(bool(br[0]["neutral"]))
	assert_true(bool(br[1]["neutral"]), "lap 1 block 1 has no cues (bars 44 to 48)")
	assert_true(bool(br[1]["passed"]), "a neutral block passes")
	assert_near(float(br[1]["energy"]), float(br[0]["energy"]), 1e-12, "and gives no energy")
	assert_eq(int(br[1]["next_stage"]), int(br[1]["stage"]), "and does not step the stage")
	assert_eq(int(br[2]["stage"]), int(br[1]["stage"]))
	assert_eq(int(br[0]["next_stage"]), 1, "a passed block with cues steps it, as ever")
	assert_true(float(br[2]["energy"]) > float(br[1]["energy"]))
	Fx.clear()


func test_the_track_energy_numbers_drive_a_track_scenes_blocks() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var et: Dictionary = d.cfg["energy"].get("track", {})
	assert_false(et.is_empty(), "run.json has energy.track")
	var e := _engine(d, "warehouse")
	var miss := func(n: Dictionary) -> bool: return int(n["phase"]) == 1 and int(n["block"]) == 1
	var log := _play(e, func(en: RunEngine) -> bool: return en.lap >= 2, miss)
	var br := _of(log, "block_result")
	var pc := float(d.cfg["judgement"]["pass_credit"])
	var en: Dictionary = (d.cfg["energy"] as Dictionary).duplicate()
	en.merge(et, true)
	var start := float(d.cfg["energy"]["start"])
	var want0 := minf(start + float(en["pass_gain"]) + float(en["pass_bonus"]) * (float(br[0]["credit"]) - pc) / (1.0 - pc), float(en["max"]))
	assert_near(float(br[0]["energy"]), want0, 1e-9, "a pass: energy.track's pass_gain and pass_bonus")
	var want1 := want0 - (float(en["fail_loss"]) * (pc - float(br[1]["credit"])) / pc + float(en.get("fail_flat", 3.0)))
	assert_near(float(br[1]["energy"]), want1, 1e-9, "a fail: energy.track's fail_loss and fail_flat")
	Fx.clear()


# --- tempo between scenes ---------------------------------------------------------------------------------------------------------

func test_the_tempo_changes_on_each_scenes_downbeat_track_to_ordinary_to_another_track() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	Fx.write_pack("slow_one", {"bpm": 128.0, "bars": 160, "cue_bars": [20, 100], "first_downbeat_s": 0.25, "sections": [["d1", "drop", 40, 100]]})
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back", "laps": 2}, "warehouse.chill": {"track": "slow_one", "laps": 2}}})
	var e := _engine(d, "warehouse")
	var b1 := 60.0 / 174.0032
	var b3 := 60.0 / 128.0
	var t1 := 128.0 * b1
	var t2 := t1 + 64.0 * B174
	var t3 := t2 + 128.0 * b3
	var beats := {}
	var at := func(en: RunEngine, _t: float) -> void:
		beats[en.phase_n] = en.beat_s
	var log := _play(e, _scene_is(4), Callable(), at)
	var ps := _of(log, "phase_start")
	assert_eq(ps.map(func(x: Dictionary) -> String: return str(x["node"])), ["warehouse", "warehouse.bar", "warehouse.chill", "warehouse.exit"])
	assert_near(float(ps[1]["t"]), t1, 1e-9, "the ordinary scene starts after two laps of the track's beat")
	assert_near(float(ps[2]["t"]), t2, 1e-9, "the second track scene after 64 beats of 174")
	assert_near(float(ps[3]["t"]), t3, 1e-9, "and lasts two laps of 128")
	assert_near(float(beats[1]), b1, 1e-12)
	assert_near(float(beats[3]), B174, 1e-12)
	assert_near(float(beats[4]), b3, 1e-12)
	assert_near(e.beat_s, B174, 1e-12, "the scene after the slow track is at 174 again")
	var tempos := _of(log, "tempo")
	assert_eq(tempos.size(), 4)
	var want_bpm := [174.0032, 174.0, 128.0, 174.0]
	for i in mini(tempos.size(), 4):
		assert_near(float(tempos[i]["bpm"]), float(want_bpm[i]), 1e-9, "tempo %d" % i)
	assert_near(float(tempos[2]["t"]), t2, 1e-9)
	assert_true(_on_grid(e, 3, 3, t1, B174), "the ordinary scene's cues are on its own 174 grid")
	assert_true(_on_grid(e, 6, 6, t3, B174), "and so are the next one's, after the slow track")
	var plan2 := d.track_scenes.plan_of("warehouse.chill")
	for n in e.level.notes:
		if int(n["phase"]) in [4, 5]:
			assert_near(float(n["time"]), t2 + float(n["track_t"]) - float(plan2["entry_t"]), 1e-9, "the slow track's cues sit where its audio plays them")
	for x in _of(log, "block_result"):
		var bs := b1 if str(x["node"]) == "warehouse" else (b3 if str(x["node"]) == "warehouse.chill" else B174)
		var t0 := 0.0 if str(x["node"]) == "warehouse" else (t1 if str(x["node"]) == "warehouse.bar" else (t2 if str(x["node"]) == "warehouse.chill" else t3))
		var lap_k := int(x["lap"])
		assert_near(float(x["t"]), t0 + (float(lap_k - 1) * 64.0 + 16.0 * float(x["block"]) + 12.5) * bs, 1e-9, "block %d of %s judged on its own beat" % [int(x["block"]), x["node"]])
	var ticks: Array = e.level.notes.map(func(n: Dictionary) -> int: return int(n["tick"]))
	var sorted := ticks.duplicate()
	sorted.sort()
	assert_eq(ticks, sorted, "ticks keep growing")
	Fx.clear()


func test_a_path_engine_arriving_in_a_track_scene_and_leaving_by_the_pause_menu() -> void:
	Fx.clear()
	Fx.write_pack("in_the_clouds", {"bpm": 96.5, "bars": 140, "cue_bars": [20, 100], "sections": [["d1", "drop", 40, 100]]})
	var pd := RunData.load_path("gospel", 7)
	RunTrackScenes.load_for(pd, Fx.write_scenes({"gospel": {"jordan": {"track": "in_the_clouds", "laps": 2}}}), Fx.root())
	assert_eq(pd.errors, [])
	var pe := RunEngine.new(pd)
	pe.hotspots = RunHotspots.new(pd, {}, {})
	var t0 := 22.0627
	pe.arrive("jordan", t0, 55.0, 3)
	var beat := 60.0 / 96.5
	assert_near(pe.beat_s, beat, 1e-12, "the track's tempo, not the path's 124")
	assert_near(pe.grid_origin, t0, 1e-12)
	var plan := pd.track_scenes.plan_of("jordan")
	for n in pe.level.notes:
		assert_near(float(n["time"]), t0 + float(n["track_t"]) - float(plan["entry_t"]), 1e-9)
	var log := _play(pe, _scene_is(5), Callable(), Callable(), t0 - 0.5)
	var ps := _of(log, "phase_start")
	assert_eq(int(ps[0]["phase"]), 4, "the phase count carries on")
	assert_near(float(ps[1]["t"]), t0 + 128.0 * beat, 1e-9, "two laps of the track")
	assert_near(pe.beat_s, 60.0 / 124.0, 1e-12, "the path's own tempo again in its next scene")
	assert_true(_on_grid(pe, 6, 6, t0 + 128.0 * beat, 60.0 / 124.0), "its cues on the 124 grid from its downbeat")
	# leaving by the pause menu in a track scene's first lap hands off on the lap's downbeat
	var pe2 := RunEngine.new(pd)
	pe2.hotspots = RunHotspots.new(pd, {}, {})
	pe2.arrive("jordan", t0, 55.0, 3)
	var leave := func(en: RunEngine, t: float) -> void:
		if en.phase_beat_at(t) > 62.0:
			en.force_leave()
	var log2 := _play(pe2, func(_en: RunEngine) -> bool: return false, Callable(), leave, t0 - 0.5, 200.0)
	var ho := _of(log2, "path_handoff")
	assert_eq(ho.size(), 1)
	assert_near(float(ho[0]["t"]), t0 + 64.0 * beat, 1e-9, "at the end of lap 1")
	var te := _of(log2, "track_end")
	assert_eq(str(te[0]["reason"]), "handoff")
	Fx.clear()


# --- a hold past the plan ----------------------------------------------------------------------------------------------------------

func test_a_hold_keeps_the_laps_counting_and_wraps_the_track_to_the_entry_bar() -> void:
	Fx.clear()
	# 100 bars, drop1 at 56: entry bar 40, plan 2 laps (half-way is behind bar 56); lap 3 is bars 72 to 88; lap 4 would be 88 to 104, past the end: the track starts again from bar 40.
	Fx.write_pack("short_one", {"bpm": 170.0, "bars": 100, "cue_bars": [30, 99], "sections": [["d1", "drop", 56, 100]]})
	var d := Fx.main_data({"main": {"warehouse": {"track": "short_one"}}})
	var plan := d.track_scenes.plan_of("warehouse")
	assert_eq(int(plan["laps"]), 2)
	var e := _engine(d, "warehouse")
	var beat := e.beat_s
	var lap_s := 64.0 * beat
	var held := func(en: RunEngine, _t: float) -> void:
		en.hold = en.lap <= 4
	var log := _play(e, _scene_is(2), Callable(), held)
	assert_eq(_of(log, "phase_start").size(), 2, "the scene is never re-entered")
	var ext := _of(log, "track_extend")
	assert_eq(ext.map(func(x: Dictionary) -> int: return int(x["laps"])), [3, 4, 5], "one more lap at the end of each held final lap")
	var wraps := _of(log, "track_wrap")
	assert_eq(wraps.size(), 1)
	assert_eq(int(wraps[0]["lap"]), 4)
	assert_near(float(wraps[0]["t"]), 3.0 * lap_s, 1e-9, "due at lap 4's downbeat")
	assert_near(float(wraps[0]["track_t"]), float(plan["entry_t"]), 1e-9, "back to the entry bar")
	assert_near(float(wraps[0]["from_track_t"]), float(plan["entry_t"]) + 3.0 * lap_s, 1e-9)
	assert_true(float(wraps[0]["decided_t"]) < float(wraps[0]["t"]))
	var tl := _of(log, "track_lap")
	assert_eq(tl.map(func(x: Dictionary) -> int: return int(x["lap"])), [2, 3, 4, 5])
	assert_near(float(tl[1]["track_t"]), float(plan["entry_t"]) + 2.0 * lap_s, 1e-9, "lap 3 goes on into the track (bars 72 to 88)")
	assert_near(float(tl[2]["track_t"]), float(plan["entry_t"]), 1e-9, "lap 4 starts again at bar 40")
	assert_near(float(tl[3]["track_t"]), float(plan["entry_t"]) + lap_s, 1e-9)
	var l1: Array = e.level.notes.filter(func(n: Dictionary) -> bool: return int(n["phase"]) == 1)
	var l4: Array = e.level.notes.filter(func(n: Dictionary) -> bool: return int(n["phase"]) == 4)
	assert_eq(l4.size(), l1.size(), "the wrapped lap plays lap 1's cues again")
	for i in mini(l1.size(), l4.size()):
		assert_near(float(l4[i]["time"]) - float(l1[i]["time"]), 3.0 * lap_s, 1e-9)
		assert_eq(int(l4[i]["pad"]), int(l1[i]["pad"]))
	assert_eq(_of(log, "hotspot_commit").size(), 1, "the hold commits nothing; released in lap 5, the default exit commits at its end")
	var rc := _of(log, "route_commit")
	assert_near(float(rc[0]["t"]), 5.0 * lap_s, 1e-9)
	for x in _of(log, "track_end"):
		assert_near(float(x["track_t"]), float(plan["entry_t"]) + 2.0 * lap_s, 1e-9, "the track is at the end of lap 5's bars")
	Fx.clear()
