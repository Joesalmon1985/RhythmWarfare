extends TestCase
## `blend` and `halftime_blend` through the whole engine (tests/fixtures/transition/blend_rig.gd: RunEngine, TransitionDirector with plan_full, RunAudio and RunTrackAudio on fixture packs,
## a virtual clock): the order of the signals, the incoming group started on the boundary's downbeat at its own tempo and never rate-changed while heard, the tail at the recipe's rate and level,
## its stems fading by kind, the high-pass rising, the hard floor at complete_t at least 4 bars before the incoming drop, `completed` then, song_time() never going back. Also the director's
## inputs to the planner, and that with the modes off nothing changes but the start.

const Rig := preload("res://tests/fixtures/transition/blend_rig.gd")


func _rig(bpms: Array, modes := 1, extra := {}) -> RefCounted:
	var chain: Array = []
	for i in bpms.size():
		chain.append({"track": "bl_%d" % i, "spec": Rig.spec(float(bpms[i]), 32, 128, extra.get(i, {}))})
	return Rig.new(tree, chain, modes)


func _seq(dir: TransitionDirector, id: int) -> Array:
	var out: Array = []
	for e in dir.log:
		var a: Array = e["args"]
		if e["signal"] == &"tempo_changed":
			out.append(&"tempo_changed")
		elif not a.is_empty() and int(a[0]) == id:
			out.append(e["signal"])
	return out


func test_a_blend_from_174_to_171() -> void:
	var rig := _rig([174.0, 171.0])
	rig.sample = true
	rig.run_transitions(1)
	rig.advance(0.5)
	var dir: TransitionDirector = rig.director
	var locks: Array = rig.signals(&"locked")
	assert_eq(locks.size(), 1)
	var la: Array = locks[0]["args"]
	var id := int(la[0])
	var plan: Dictionary = la[3]
	var T := float(la[2])
	assert_eq(plan["mode"], &"blend")
	assert_false(bool(plan["fallback"]))
	var bar_in := 240.0 / 171.0
	assert_eq(int(plan["blend_beats"]), 48, "W = 12 bars (16 bars of lead-in less the 4 clear ones)")
	assert_near(float(plan["complete_t"]), T + 12.0 * bar_in, 1e-6)
	var keys: Array = plan.keys()
	keys.sort()
	var want := TransitionPlanner.plan_keys()
	want.sort()
	assert_eq(keys, want, "the Plan has the contract's keys only")
	assert_eq(_seq(dir, id), [&"request_acknowledged", &"locked", &"tempo_changed", &"switched", &"completed"], "tempo_changed before switched, completed last")
	var recipe: Dictionary = dir.lock_log[0]["recipe"]
	var rate := 171.0 / 174.0
	assert_near(float(recipe["rate"]), rate, 1e-9)
	assert_eq(str((recipe["in"] as Dictionary)["track"]), "bl_1", "the audio is told the incoming track")
	assert_eq(str((recipe["out"] as Dictionary)["track"]), "bl_0")
	var drop_t := float(recipe["drop_t"])
	assert_near(drop_t, T + 16.0 * bar_in, 1e-6, "the incoming drop: 16 bars after T")
	# the incoming started early, muted, and was adopted
	var st: Array = rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")
	assert_eq(st.size(), 2)
	assert_true(bool(st[1]["prepared"]), "the incoming group was started at the lock, muted")
	assert_near(float(st[1]["t"]), T, 1e-9, "its scene begins on T")
	# the frames
	var prev_song := -INF
	var saw_tail := false
	var floor_seen := false
	for f in rig.frames:
		var x := float(f["t"])
		assert_true(float(f["song_time"]) >= prev_song - 1e-12, "song_time() never decreases")
		prev_song = float(f["song_time"])
		for g in f["groups"]:
			if str(g["track"]) == "bl_1" and not bool(g["pending"]):
				assert_eq(float(g["rate"]), 1.0, "the incoming is never rate-changed while heard (t=%.3f)" % x)
				assert_near(float(g["volume_db"]), 0.0, 1e-9, "and plays at its own level")
		for tl in f["tails"]:
			saw_tail = true
			var b := (x - T) / bar_in
			assert_near(float(tl["rate"]), rate, 1e-6, "the tail at rho")
			assert_near(float(tl["volume_db"]), TransitionPlanner.TAIL_GAIN_DB, 1e-9, "the tail's level from T")
			var gn: Dictionary = tl["gains"]
			if b >= 1.0:
				assert_eq(float(gn["bass"]), 0.0, "bass gone by bar 1 (b=%.2f)" % b)
			if b >= 2.0:
				assert_eq(float(gn["drums"]), 0.0, "drums gone by bar 2")
				assert_eq(float(gn["backing"]), 0.0, "backing (rhythm) gone by bar 2")
			if b < 2.0:
				assert_near(float(gn["other"]), 1.0, 1e-9, "the synths hold to bar 2")
			if b > 0.05 and b < 0.95:
				assert_true(float(gn["bass"]) > 0.0 and float(gn["bass"]) < 1.0, "bass mid-fade")
			assert_true(bool(tl["hp_on"]), "the tail's high-pass is on")
			assert_near(float(tl["cutoff"]), 20.0 * pow(250.0 / 20.0, clampf(b / 4.0, 0.0, 1.0)), 0.5 + 0.05 * 250.0 * (1.0 / 60.0) / bar_in, "rising 20 to 250 Hz over 4 bars")
			assert_true(x < float(plan["complete_t"]) + 1e-6, "no tail after complete_t")
			assert_true(x <= drop_t - 4.0 * bar_in + 1e-6, "the hard floor: nothing of the tail in the 4 bars before the drop")
		if x > float(plan["complete_t"]) + 0.02 and f["tails"].is_empty():
			floor_seen = true
	assert_true(saw_tail, "a tail played")
	assert_true(floor_seen, "and was gone after complete_t")
	var fl: Array = rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "floor")
	assert_eq(fl.size(), 1)
	assert_near(float(fl[0]["at"]), float(plan["complete_t"]), 1.0 / 60.0 + 1e-6, "the floor at complete_t")
	assert_eq(fl[0]["still_sounding"], [], "every curve was down by the floor")
	var co: Array = rig.signals(&"completed")
	assert_near(float(co[0]["t"]), float(plan["complete_t"]), 1.0 / 60.0 + 1e-6, "completed when the tail is silent")
	assert_true(float(co[0]["t"]) <= drop_t - 4.0 * bar_in + 1e-6, "before the drop's 4 clear bars")
	var bus := AudioServer.get_bus_index(str(RunTrackAudio.SLOT_BUSES[0]))
	assert_false(AudioServer.is_bus_effect_enabled(bus, RunTrackAudio.FX_HIGHPASS), "the slot's effects off after the floor")
	assert_eq(rig.audio.track.active_group_count(), 1, "the tail's group is freed: one group plays")
	rig.free_all()


func test_tail_beats_sit_on_the_incoming_grid() -> void:
	# the accounting of the tail: track time at song time x is out_t(T) + rate (x - T); its bar lines fall on the incoming bar lines
	var rig := _rig([175.0, 172.0])
	rig.run_transitions(1)
	var la: Array = rig.signals(&"locked")[0]["args"]
	var T := float(la[2])
	var out_plan: Dictionary = rig.data.track_scenes.plan_of("tx0")
	var out_t := float(out_plan["entry_t"]) + 2.0 * float(out_plan["lap_s"])
	var rate: float = rig.director.lock_log[0]["recipe"]["rate"]
	var bar_out := 240.0 / 175.0
	var bar_in := 240.0 / 172.0
	for k in 13:
		var x := T + float(k) * bar_in
		var tail_bar := (out_t + rate * (x - T) - float(out_plan["first_downbeat_s"])) / bar_out
		assert_near(tail_bar - roundf(tail_bar), 0.0, 1e-6, "incoming bar %d is a tail bar line" % k)
	rig.free_all()


func test_halftime_blend_on_fixture_packs() -> void:
	var rig := _rig([88.0, 174.0])
	rig.sample = true
	rig.run_transitions(1)
	var la: Array = rig.signals(&"locked")[0]["args"]
	assert_eq((la[3] as Dictionary)["mode"], &"halftime_blend", "88 to 174: rho 1.977, half of it within 50 cents")
	var recipe: Dictionary = rig.director.lock_log[0]["recipe"]
	assert_near(float(recipe["rate"]), 174.0 / 88.0 / 2.0, 1e-9, "the tail at rho / 2")
	var rates: Array = []
	for f in rig.frames:
		for tl in f["tails"]:
			rates.append(float(tl["rate"]))
	assert_true(not rates.is_empty())
	assert_near(float(rates[0]), 174.0 / 88.0 / 2.0, 1e-6)
	assert_eq(rig.signals(&"completed").size(), 1)
	rig.free_all()


func test_the_director_gives_the_planner_its_full_inputs() -> void:
	var rig := _rig([175.0, 172.0])
	var seen: Array = []
	var dir: TransitionDirector = rig.director
	dir.planner = func(o: Dictionary, i: Dictionary, m: Dictionary, r: Dictionary) -> Dictionary:
		seen.append([o.duplicate(), i.duplicate(), m.duplicate(), r.duplicate()])
		return TransitionPlanner.plan(o, i, m, r)
	rig.run_transitions(1)
	assert_eq(seen.size(), 1)
	var o: Dictionary = seen[0][0]
	var i: Dictionary = seen[0][1]
	var m: Dictionary = seen[0][2]
	var op: Dictionary = rig.data.track_scenes.plan_of("tx0")
	var ip: Dictionary = rig.data.track_scenes.plan_of("tx1")
	assert_eq(o["kind"], &"track")
	assert_eq(str(o["track"]), "bl_0")
	assert_near(float(o["duration_s"]), float(op["duration_s"]), 1e-9)
	assert_near(float(o["track_t_at_T"]), float(op["entry_t"]) + 2.0 * float(op["lap_s"]), 1e-6, "where the outgoing track is at T (the end of lap 2)")
	assert_near(float(o["first_downbeat_s"]), 0.05, 1e-9)
	assert_eq(str(o["section_role"]), "drop", "bar 48 lies in the drop (bars 32 to 80)")
	assert_eq(o["stem_keys"], ["drums", "bass", "other", "backing"])
	assert_eq(str(i["track"]), "bl_1")
	assert_eq(int(i["entry_bar"]), 16)
	assert_eq(int(i["drop_bar"]), 32)
	assert_eq(int(ip["drop_bar"]), 32)
	assert_true(bool(m["out_grid_ok"]) and bool(m["in_grid_ok"]))
	assert_eq(str(m["out_state"]), "missing", "no sidecar for a fixture track")
	assert_eq(m["out"], {})
	assert_eq(bool(m["modes_enabled"]), true, "the rig's director plans every mode")
	assert_eq(str(seen[0][3]["state"]), "ready")
	rig.free_all()


func test_with_the_modes_off_every_change_is_a_cut_with_the_start_fix() -> void:
	var rig := _rig([174.0, 171.0], 0)
	rig.run_transitions(1)
	var la: Array = rig.signals(&"locked")[0]["args"]
	assert_eq((la[3] as Dictionary)["mode"], &"cut")
	assert_eq(rig.audio.track.tail_count(), 0)
	var ends: Array = rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "end")
	assert_eq(ends.size(), 1, "the outgoing faded as today")
	assert_near(float(ends[0]["seconds"]), 0.6, 1e-9)
	var st: Array = rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "start")
	assert_true(bool(st[1]["prepared"]), "but started early and muted")
	assert_eq(rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "tail"), [])
	rig.free_all()


func test_a_pause_in_the_middle_of_a_blend_freezes_it() -> void:
	# the fades are functions of song time: song time stopping (a pause, a lost focus) stops them; RunAudio.pause pauses every player in one lock
	var rig := _rig([174.0, 171.0])
	var dir: TransitionDirector = rig.director
	while rig.signals(&"switched").is_empty():
		rig.advance(0.25)
	rig.advance(1.0)
	var tails: Array = rig.audio.track._groups.filter(func(g: Dictionary) -> bool: return not (g["tail"] as Dictionary).is_empty())
	assert_eq(tails.size(), 1)
	var tr: TrackTransport = tails[0]["transport"]
	var before := tr.tail_gain("bass")
	rig.audio.pause()
	for g in rig.audio.track._groups:
		assert_true((g["transport"] as TrackTransport).player.stream_paused, "every group paused, the tail too")
	for _k in 30:  # (frames go by, song time does not)
		rig.audio.track.step(rig.t, 0.0)
	assert_near(tr.tail_gain("bass"), before, 1e-12, "the tail's fades stand still")
	rig.audio.resume()
	for g in rig.audio.track._groups:
		assert_false((g["transport"] as TrackTransport).player.stream_paused)
	rig.run_transitions(1)
	assert_eq(dir.log.filter(func(e: Dictionary) -> bool: return e["signal"] == &"completed").size(), 1, "the blend then completes")
	rig.free_all()
