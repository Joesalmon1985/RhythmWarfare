extends TestCase
## Track scenes, the audio half (RunTrackAudio under RunAudio, docs/RUN_TRACK_SCENES.md "Audio") on synthetic fixture packs: the engine runs on a virtual clock and every event goes to a real
## RunAudio, whose scheduled items run at their own song time (no lateness unless a test says so). The track's stems start as one group from the entry bar at the pack's gains on the RunTrack bus,
## no loop starts in a track scene, the group plays on across laps, wraps by a seek, fades at the end and on the Bassment's entry; a pack not ready makes an ordinary scene; mutes follow the run's
## judge; the hotspot dip lowers the stems that are not drums; the loader keeps only what is needed; ordinary scenes before and after a track scene start the same voices as without it; the clock is
## tempo-free (48 kHz) with track scenes on and the old per-tempo loop with them off.

const Fx := preload("res://tests/fixtures/track_scenes/track_scene_fixtures.gd")

var _made: Array = []


func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	_made.append(a)
	return a


func _cleanup() -> void:
	for a in _made:
		if is_instance_valid(a):
			(a as RunAudio).stop()
			(a as RunAudio).free()
	_made.clear()
	Fx.clear()


func _engine(d: RunData, a: RunAudio, start: String, prepare := true) -> RunEngine:
	assert_eq(d.errors, [], "the run data validates")
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	if a != null:
		e.track_gate = a.track.is_ready
		a.track.notes_fn = func() -> Array: return e.level.notes
		if prepare:
			a.track.prepare(d, start)
	e.begin(start)
	return e


## Waits for the decodes under way (worker threads) and takes them.
func _wait_loads(a: RunAudio) -> void:
	for _i in 400:
		a.track._poll()
		if not a.track.cached().values().has("loading"):
			return
		OS.delay_msec(5)


## Runs RunAudio's and the track's items due by `t`, as their frame would.
func _pump(a: RunAudio, t: float) -> void:
	for path in a._requested:  # (the loops' threaded loads: done before their voices start, as frames would have let them)
		for _i in 400:
			if ResourceLoader.load_threaded_get_status(str(path)) != ResourceLoader.THREAD_LOAD_IN_PROGRESS:
				break
			OS.delay_msec(5)
	while not a._schedule.is_empty() and float(a._schedule[0]["t"]) <= t:
		var item: Dictionary = a._schedule.pop_front()
		a._run(item, float(item["t"]), 0.0)  # (each at its own time: no lateness on the virtual clock)
	while not a.track._schedule.is_empty() and float(a.track._schedule[0]["t"]) <= t:
		var it: Dictionary = a.track._schedule.pop_front()
		a.track.run_item(it, float(it["t"]), 0.0)
	a.track.step(t, 0.0)


## Plays `e` with a perfect player (but the cues `miss(note)` names) until `stop(e)`, every event to `a` (the route windows prefetch as RunPlay does), `at(e, t)` each frame. Returns the events.
func _run(e: RunEngine, a: RunAudio, stop: Callable, miss: Callable = Callable(), at: Callable = Callable(), max_s := 900.0) -> Array:
	var log: Array = []
	var next_i := 0
	var down := {}
	var t := -0.5
	while t < max_s and not e.over and e.away == "" and not bool(stop.call(e)):
		if at.is_valid():
			at.call(e, t)
		var evs := e.update(t)
		for ev in evs:
			if a != null:
				a.on_event(ev)
				if str(ev["kind"]) == "route_window":
					a.track.prefetch_for(e.data, e.node_id)
					_wait_loads(a)
		log.append_array(evs)
		if a != null:
			_pump(a, t)
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


func _go_back() -> Dictionary:
	return Fx.go_back_spec()


# --- the group ----------------------------------------------------------------------------------------------------------------

func test_the_track_plays_as_one_group_from_its_entry_bar_across_laps_and_fades_at_the_end() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var a := _audio(d)
	var e := _engine(d, a, "warehouse")
	var plan := d.track_scenes.plan_of("warehouse")
	var lap_s := 64.0 * e.beat_s
	assert_true(e.is_track_scene(), "the stems were decoded before the run: a track scene")
	assert_eq((a.track.load_log as Array).size(), 1)
	assert_true(bool(a.track.load_log[0]["ok"]))
	var mid := [{}]
	var at := func(en: RunEngine, t: float) -> void:
		if en.lap == 3 and mid[0].is_empty():
			mid[0] = a.track.live()
	var log := _run(e, a, _scene_is(2), Callable(), at)
	var starts := a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")
	assert_eq(starts.size(), 1, "one start for the whole scene: no restart at a lap")
	assert_near(float(starts[0]["t"]), 0.0, 1e-12)
	assert_near(float(starts[0]["from"]), float(plan["entry_t"]), 1e-9, "from the entry bar's downbeat")
	assert_eq(starts[0]["stems"], ["drums", "bass", "backing"], "every stem, voices then backing")
	assert_eq(starts[0]["gains"], [1.0, 1.0, 1.0], "at the pack's gains")
	assert_eq(str(mid[0].get("track", "")), "acuna_go_back", "still the one group in lap 3")
	assert_eq(a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "seek"), [], "no wrap: no seek")
	assert_eq(a.voice_log.filter(func(v: Dictionary) -> bool: return str(v["node"]) == "warehouse"), [], "no loop voice starts in the track scene")
	assert_eq(a.voice_log.filter(func(v: Dictionary) -> bool: return str(v["voice"]) in ["riser", "fall"]), [], "no riser or fall over the track")
	var ends := a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "end")
	assert_eq(ends.size(), 1)
	assert_near(float(ends[0]["t"]), 4.0 * lap_s, 1e-9, "the track fades from the scene's last downbeat")
	assert_eq(str(ends[0]["reason"]), "route")
	assert_near(float(ends[0]["seconds"]), float(d.cfg["mix"]["phase_fade_s"]), 1e-9, "over the run's phase fade, as a scene's music")
	var drums_next := a.voice_log.filter(func(v: Dictionary) -> bool: return str(v["node"]) == "warehouse.bar" and str(v["voice"]) == "drums")
	assert_eq(drums_next.size(), 1)
	assert_near(float(drums_next[0]["target"]), 4.0 * lap_s, 1e-9, "the next scene's loops start on their own downbeat, the same one")
	assert_eq(a.track.active_group_count(), 1, "the faded group is still there until its fade has run (no frames here)")
	var tr: TrackTransport = a.track._groups[0]["transport"]
	assert_eq(tr.player.bus, RunTrackAudio.BUS)
	var bi := AudioServer.get_bus_index(RunTrackAudio.BUS)
	assert_true(bi >= 0)
	assert_eq(str(AudioServer.get_bus_send(bi)), "Music", "the track bus feeds the music bus")
	var lim := false
	for k in AudioServer.get_bus_effect_count(bi):
		lim = lim or AudioServer.get_bus_effect(bi, k) is AudioEffectHardLimiter
	assert_true(lim, "through a limiter")
	assert_eq(_of(log, "track_start").size(), 1)
	_cleanup()


func test_a_late_start_begins_as_far_into_the_track_as_it_is_late() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var a := _audio(d)
	var e := _engine(d, a, "warehouse")
	for ev in e.update(-5.0):
		a.on_event(ev)
	var item: Dictionary = a.track._schedule.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")[0]
	a.track.run_item(item, 0.012, 0.009)
	var s: Dictionary = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")[0]
	var plan := d.track_scenes.plan_of("warehouse")
	assert_near(float(s["from"]), float(plan["entry_t"]) + 0.021, 1e-9, "the call is 21 ms late (now + time to the next mix): the stems start 21 ms in")
	assert_near(float(s["lateness_ms"]), 21.0, 1e-6, "the start lag is logged")
	var tr: TrackTransport = a.track._groups[0]["transport"]
	assert_near(tr.start_at, float(plan["entry_t"]) + 0.021, 1e-9)
	assert_true(tr.player.playing)
	_cleanup()


func test_a_hold_past_the_plan_seeks_the_group_back_to_the_entry_bar() -> void:
	Fx.clear()
	Fx.write_pack("short_one", {"bpm": 170.0, "bars": 100, "cue_bars": [30, 99], "sections": [["d1", "drop", 56, 100]]})
	var d := Fx.main_data({"main": {"warehouse": {"track": "short_one"}}})
	var a := _audio(d)
	var e := _engine(d, a, "warehouse")
	var plan := d.track_scenes.plan_of("warehouse")
	var lap_s := 64.0 * e.beat_s
	var held := func(en: RunEngine, _t: float) -> void:
		en.hold = en.lap <= 4
	_run(e, a, _scene_is(2), Callable(), held)
	var seeks := a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "seek")
	assert_eq(seeks.size(), 1)
	assert_near(float(seeks[0]["t"]), 3.0 * lap_s, 1e-9, "on lap 4's downbeat")
	assert_near(float(seeks[0]["track_t"]), float(plan["entry_t"]), 1e-9, "back to the entry bar")
	assert_eq(a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start").size(), 1, "a seek, not a new group")
	_cleanup()


func test_entering_the_bassment_fades_the_track_without_a_track_end() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var a := _audio(d)
	var e := _engine(d, a, "warehouse")
	var t_in := 20.0 * e.beat_s + 3.25 * e.beat_s
	var log := _run(e, a, func(en: RunEngine) -> bool: return en.phase_beat_at(t_in) < 0.0 or false, Callable(), Callable(), t_in - 0.1)
	assert_eq(a.track.active_group_count(), 1)
	a.track.on_event({"kind": "phase_start", "node": "trial", "phase": 2, "t": t_in, "treatment": "none", "audio": "x"})  # (what TrialScene.begin hands RunAudio on the Bassment's downbeat)
	_pump(a, t_in)
	var ends := a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "end")
	assert_eq(ends.size(), 1, "the track fades on the dungeon's downbeat")
	assert_near(float(ends[0]["t"]), t_in, 1e-9)
	assert_eq(str(ends[0]["reason"]), "scene")
	assert_eq(_of(log, "track_end"), [], "the engine sent no track_end")
	assert_true(bool(a.track._groups[0]["fading"]))
	_cleanup()


func test_a_pack_not_ready_in_time_makes_an_ordinary_scene() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var a := _audio(d)
	var e := _engine(d, a, "warehouse", false)
	assert_false(e.is_track_scene(), "nothing decoded: the scene plays its loops")
	assert_eq(e.track_gate_answer("warehouse"), 0, "the answer is latched for the visit")
	assert_near(e.beat_s, 60.0 / 174.0, 1e-12, "at the run's tempo")
	var nr := a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "not_ready")
	assert_eq(nr.size(), 1)
	var log := _run(e, a, _scene_is(2))
	assert_eq(_of(log, "track_start"), [])
	assert_true(a.voice_log.filter(func(v: Dictionary) -> bool: return str(v["node"]) == "warehouse" and str(v["voice"]) == "drums").size() >= 1, "the loops play")
	assert_eq(a.track.active_group_count(), 0)
	_cleanup()


func test_the_next_scene_becomes_a_track_scene_when_its_stems_load_after_the_doors_open() -> void:
	Fx.clear()
	Fx.write_pack("bar_track", {"bpm": 168.0, "bars": 160, "cue_bars": [20, 150], "sections": [["d1", "drop", 56, 96]]})
	var d := Fx.main_data({"main": {"warehouse.bar": {"track": "bar_track"}}})
	var a := _audio(d)
	var e := _engine(d, a, "warehouse")
	var log := _run(e, a, _scene_is(2))
	assert_eq(e.node_id, "warehouse.bar")
	assert_true(e.is_track_scene(), "decoded on a worker thread from the warehouse's route window, before the route lock")
	assert_eq(e.track_gate_answer("warehouse.bar"), 1)
	assert_eq(a.track.cached().keys(), [Fx.root().path_join("bar_track")], "only the candidate is in memory")
	_pump(a, e.phase_t0 + 0.001)
	assert_eq(str(a.track.live().get("track", "")), "bar_track")
	assert_eq(_of(log, "tempo").size(), 1)
	_cleanup()


# --- an ordinary scene before and after ----------------------------------------------------------------------------------------

## The voices RunAudio started for scene `node`, relative to its downbeat: [voice, pack, section, target - t0].
func _voices_of(a: RunAudio, node: String, t0: float) -> Array:
	return a.voice_log.filter(func(v: Dictionary) -> bool: return str(v["node"]) == node).map(func(v: Dictionary) -> Array:
		return [str(v["voice"]), str(v.get("pack", "")), int(v.get("section", 0)), snappedf(float(v["target"]) - t0, 1e-9)])


func test_ordinary_scenes_before_and_after_a_track_scene_start_the_same_voices_as_without_it() -> void:
	Fx.clear()
	Fx.write_pack("bar_track", {"bpm": 168.0, "bars": 160, "cue_bars": [20, 150], "sections": [["d1", "drop", 56, 96]]})
	var plain := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7)  # (the seed Fx.main_data uses: the same arrangement picks)
	var a0 := _audio(plain)
	var e0 := _engine(plain, a0, "warehouse")
	_run(e0, a0, _scene_is(3))
	var t0_chill := e0.phase_t0
	_pump(a0, t0_chill + 30.0 * e0.beat_s)
	var d := Fx.main_data({"main": {"warehouse.bar": {"track": "bar_track"}}})
	var a1 := _audio(d)
	var e1 := _engine(d, a1, "warehouse")
	var log := _run(e1, a1, _scene_is(3))
	assert_eq(_of(log, "track_start").size(), 1, "the bar was a track scene")
	assert_eq(e1.node_id, e0.node_id, "the same route")
	var t1_chill := e1.phase_t0
	_pump(a1, t1_chill + 30.0 * e1.beat_s)
	assert_eq(_voices_of(a1, "warehouse", 0.0), _voices_of(a0, "warehouse", 0.0), "the scene before: the same voices at the same times")
	var after0 := _voices_of(a0, e0.node_id, t0_chill)
	assert_true(after0.size() >= 1)
	assert_eq(_voices_of(a1, e1.node_id, t1_chill), after0, "the scene after: the same voices, from its own downbeat")
	assert_eq(a1.voice_log.filter(func(v: Dictionary) -> bool: return str(v["node"]) == "warehouse.bar"), [], "none in the track scene")
	assert_near(e1.beat_s, e0.beat_s, 1e-12, "back at the run's tempo")
	_cleanup()


# --- mutes, the dip -------------------------------------------------------------------------------------------------------------

func test_a_missed_cue_mutes_its_voice_and_the_next_hit_brings_it_back() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var a := _audio(d)
	var e := _engine(d, a, "warehouse")
	var beat := e.beat_s
	var seen := {"muted": false, "back": false}
	var miss := func(n: Dictionary) -> bool: return int(n["phase"]) == 1 and int(n["block"]) == 1 and float(n["time"]) > 22.0 * beat  # (the last few cues of block 1)
	var at := func(en: RunEngine, t: float) -> void:
		var tr: TrackTransport = a.track._groups[0]["transport"] if a.track.active_group_count() > 0 else null
		if tr == null:
			return
		if t > 28.6 * beat and t < 31.0 * beat and tr.is_stem_muted("drums"):
			seen["muted"] = true
			assert_false(tr.is_stem_muted("bass"), "only the missed cue's voice")
			assert_false(tr.is_stem_muted("backing"), "backing never mutes")
		if t > 33.0 * beat and t < 34.0 * beat and seen["muted"]:
			seen["back"] = not tr.is_stem_muted("drums")
	_run(e, a, func(en: RunEngine) -> bool: return en.phase_beat_at(0.0) < -40.0, miss, at, 40.0 * beat)
	assert_true(seen["muted"], "the drums' stem is silent after the misses")
	assert_true(seen["back"], "and back at the first hit of block 2 (beat 32)")
	var reasons: Array = a.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) in ["mute", "restore"]).map(func(x: Dictionary) -> String: return "%s:%s" % [x["kind"], x["reason"]])
	assert_eq(reasons, ["mute:miss", "restore:hit"])
	_cleanup()


func test_the_hotspot_dip_lowers_the_stems_that_are_not_drums_for_its_beats() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var a := _audio(d)
	var e := _engine(d, a, "warehouse")
	for ev in e.update(0.0):
		a.on_event(ev)
	_pump(a, 0.0)
	var tr: TrackTransport = a.track._groups[0]["transport"]
	a.on_event({"kind": "hotspot_commit", "t": 1.0, "block": 0, "node": "warehouse", "phase": 1, "outcome": {"music": "dip"}, "energy": 60.0})
	_pump(a, 1.0)
	assert_near(float(tr._scale_target.get("bass", 1.0)), float(d.cfg["mix"]["dip_gain"]), 1e-9, "the pitched voice dips")
	assert_near(float(tr._scale_target.get("backing", 1.0)), float(d.cfg["mix"]["dip_gain"]), 1e-9, "and the backing")
	assert_false(tr._scale_target.has("drums"), "the drums carry on")
	_pump(a, 1.0 + float(d.cfg["mix"]["dip_beats"]) * e.beat_s)
	assert_near(float(tr._scale_target["bass"]), 1.0, 1e-9, "back after dip_beats of the track's beat")
	_cleanup()


# --- the loader, the clock --------------------------------------------------------------------------------------------------------

func test_the_loader_keeps_only_the_candidates_and_reports_a_failure() -> void:
	Fx.clear()
	Fx.write_pack("bar_track", {"bpm": 168.0, "bars": 160, "cue_bars": [20, 150], "sections": [["d1", "drop", 56, 96]]})
	Fx.write_pack("balc_track", {"bpm": 160.0, "bars": 160, "cue_bars": [20, 150], "sections": [["d1", "drop", 56, 96]]})
	Fx.write_pack("chill_track", {"bpm": 150.0, "bars": 160, "cue_bars": [20, 150], "sections": [["d1", "drop", 56, 96]]})
	var d := Fx.main_data({"main": {"warehouse.bar": {"track": "bar_track"}, "warehouse.balcony": {"track": "balc_track"}, "warehouse.chill": {"track": "chill_track"}}})
	var a := _audio(d)
	a.track.prefetch_for(d, "warehouse")
	a.track.prefetch_for(d, "warehouse")  # (again while loading: nothing twice)
	_wait_loads(a)
	var c := a.track.cached()
	assert_eq(c.size(), 2, "the warehouse's two routes")
	assert_eq(c.values(), ["ready", "ready"])
	assert_eq(a.track.load_log.size(), 2, "each decoded once")
	a.track.prefetch_for(d, "warehouse.bar")  # (its routes: the chill and the booth, which has no track)
	_wait_loads(a)
	assert_eq(a.track.cached().keys(), [Fx.root().path_join("chill_track")], "the others are let go")
	# a stem that cannot be decoded
	var bad := Fx.root().path_join("bar_track").path_join("stems").path_join("bass.ogg")
	var f := FileAccess.open(bad, FileAccess.WRITE)
	f.store_string("OggS not really")
	f.close()
	a.track.prefetch_for(d, "warehouse")
	_wait_loads(a)
	assert_eq(str(a.track.cached()[Fx.root().path_join("bar_track")]), "failed")
	assert_false(bool(a.track.load_log[a.track.load_log.size() - 2]["ok"]) and bool(a.track.load_log[a.track.load_log.size() - 1]["ok"]), "the failure is logged")
	assert_false(a.track.is_ready(d.track_scenes.plan_of("warehouse.bar")), "a failed pack is never ready: the scene stays ordinary")
	_cleanup()


func test_the_clock_is_tempo_free_with_track_scenes_on_and_as_before_with_them_off() -> void:
	Fx.clear()
	Fx.write_pack("acuna_go_back", _go_back())
	var d := Fx.main_data({"main": {"warehouse": {"track": "acuna_go_back"}}})
	var a := _audio(d)
	assert_true(a.tempo_free)
	var s: AudioStreamWAV = a.player.stream
	assert_eq(s.mix_rate, int(AudioServer.get_mix_rate()), "one silent loop at the mix rate: a resampling step of exactly 1, no drift against the stems")
	assert_near(a.loop_seconds, float(RunAudio.FREE_FRAMES) / AudioServer.get_mix_rate(), 1e-12)
	var e := _engine(d, a, "warehouse")
	_run(e, a, _scene_is(2))
	assert_true(a.player.stream == s, "neither the track scene nor the scene after it swaps the clock")
	var pd := RunData.load_path("stub")
	a.schedule_clock_swap(pd, 100.0)
	var clock_item: Dictionary = a._schedule.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "clock")[0]
	a._run(clock_item, 100.0, 0.0)
	assert_true(a.player.stream == s, "nor a path hand-off: song time is one line")
	assert_true(bool(a.clock_log[a.clock_log.size() - 1]["tempo_free"]))
	var plain := _audio(RunData.load_default())
	assert_false(plain.tempo_free)
	assert_eq((plain.player.stream as AudioStreamWAV).mix_rate, 8700, "track scenes off: the 174 BPM loop as before")
	_cleanup()
