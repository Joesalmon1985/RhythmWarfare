extends TestCase
## `echo_out` through the whole engine (tests/fixtures/transition/blend_rig.gd): 140 BPM into 174 is no blend (376 cents), so the tail plays at its own rate through the slot's delay
## (3/4 of an outgoing beat, feedback 0.4) and a high-pass rising 200 to 2,000 Hz; its rhythm and bass fall in half a beat, its synths in one bar, and the hard floor at T + 2 bars stops it,
## its repeats included (the delay off, then made afresh so no echo is left in its line). Also the echo of a short lead-in (W = 1) and a grid that is not steady.

const Rig := preload("res://tests/fixtures/transition/blend_rig.gd")


func test_an_echo_out_from_140_to_174() -> void:
	var rig: RefCounted = Rig.new(tree, [{"track": "ec_a", "spec": Rig.spec(140.0)}, {"track": "ec_b", "spec": Rig.spec(174.0)}], 1)
	rig.sample = true
	rig.run_transitions(1)
	rig.advance(0.5)
	var la: Array = rig.signals(&"locked")[0]["args"]
	var plan: Dictionary = la[3]
	var T := float(la[2])
	var bar_in := 240.0 / 174.0
	assert_eq(plan["mode"], &"echo_out")
	assert_eq(int(plan["blend_beats"]), 8, "W = 2 bars")
	assert_near(float(plan["complete_t"]), T + 2.0 * bar_in, 1e-6)
	var recipe: Dictionary = rig.director.lock_log[0]["recipe"]
	assert_near(float((recipe["echo"] as Dictionary)["delay_s"]), 0.75 * 60.0 / 140.0, 1e-9, "3/4 of an outgoing beat")
	var saw := 0
	for f in rig.frames:
		var x := float(f["t"])
		for tl in f["tails"]:
			saw += 1
			var b := (x - T) / bar_in
			assert_eq(float(tl["rate"]), 1.0, "no rate matching")
			assert_true(bool(tl["delay_on"]) and bool(tl["hp_on"]), "the delay and the high-pass on")
			var gn: Dictionary = tl["gains"]
			if b >= 0.125:
				for k in ["drums", "bass", "backing"]:
					assert_eq(float(gn[k]), 0.0, "%s gone in half a beat (b=%.3f)" % [k, b])
			if b >= 1.0:
				assert_eq(float(gn["other"]), 0.0, "the synths gone in one bar")
			assert_near(float(tl["cutoff"]), 200.0 * pow(10.0, clampf(b / 2.0, 0.0, 1.0)), 1.0 + 2000.0 * 0.03, "200 to 2,000 Hz over W")
			assert_true(x < float(plan["complete_t"]) + 1e-6)
	assert_true(saw > 0)
	var tl0: Dictionary = rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "tail")[0]
	var bus := AudioServer.get_bus_index(str(RunTrackAudio.SLOT_BUSES[int(tl0["slot"])]))
	assert_false(AudioServer.is_bus_effect_enabled(bus, RunTrackAudio.FX_DELAY), "the repeats are cut at the floor")
	var dl := AudioServer.get_bus_effect(bus, RunTrackAudio.FX_DELAY) as AudioEffectDelay
	assert_false(dl.feedback_active, "a fresh delay, nothing left in its line")
	var co: Array = rig.signals(&"completed")
	assert_near(float(co[0]["t"]), float(plan["complete_t"]), 1.0 / 60.0 + 1e-6, "completed at the floor")
	rig.free_all()


func test_a_track_whose_tempo_drifts_echoes_out_instead_of_blending() -> void:
	var rig: RefCounted = Rig.new(tree, [{"track": "dr_a", "spec": Rig.spec(174.0)}, {"track": "dr_b", "spec": Rig.spec(174.0)}], 1)
	(rig.data.track_scenes.plan_of("tx1") as Dictionary)["grid_ok"] = false  # (as a drift of more than 20 ms in the pack would make it)
	rig.run_transitions(1)
	assert_eq((rig.signals(&"locked")[0]["args"][3] as Dictionary)["mode"], &"echo_out", "no beat matching without a steady grid")
	rig.free_all()


func test_a_lead_in_of_five_bars_echoes_out_in_one_bar_and_four_bars_cut() -> void:
	# lead_in_bars 5: L = 5 (the least that leaves 4 clear bars), a blend's window would be 1 bar: echo_out W = 1. lead_in_bars 4: cut (ruling 7).
	for lead in [5, 4]:
		var rig: RefCounted = Rig.new(tree, [{"track": "sl_a", "spec": Rig.spec(174.0)}, {"track": "sl_b", "spec": Rig.spec(172.0), "entry": {"lead_in_bars": lead}}], 1)
		rig.run_transitions(1)
		var la: Array = rig.signals(&"locked")[0]["args"]
		var plan: Dictionary = la[3]
		if lead == 5:
			assert_eq(plan["mode"], &"echo_out")
			assert_eq(int(plan["blend_beats"]), 4)
			var drop_t := float(la[2]) + 5.0 * 240.0 / 172.0
			assert_true(float(rig.signals(&"completed")[0]["t"]) <= drop_t - 4.0 * 240.0 / 172.0 + 1.0 / 60.0, "silent 4 bars before the drop")
		else:
			assert_eq(plan["mode"], &"cut")
			assert_eq(str(rig.director.lock_log[0]["recipe"].get("reason", "")), "short_lead")
		rig.free_all()
