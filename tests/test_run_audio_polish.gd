extends TestCase
## The audio polish (docs/HANDOVER.md "Audio polish"): the data rules and RunAudio's bass bus, run level and bass carry. Every number is data (run.json `stages` and `mix`, a path's run.json `mix`,
## a scene's music.json `bass_bus`); these tests hold the rules, not the values.


func _runs() -> Array:
	var out: Array = [RunData.load_default()]
	for id in RunData.path_ids():
		out.append(RunData.load_path(str(id), 1))
	return out


func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	return a


func _ev(d: RunData, node: String, t: float, phase: int) -> Dictionary:
	return {"kind": "phase_start", "node": node, "t": t, "phase": phase, "treatment": "none", "audio": d.nodes[node]["audio"], "temporary": false, "fresh": phase == 1, "world": d.nodes[node]["world"],
		"path": d.path_id}


func test_the_mix_settings_load_for_the_main_run_and_every_path() -> void:
	var runs := _runs()
	assert_true(runs.size() >= 4, "the main run and the paths")
	for dv in runs:
		var d: RunData = dv
		var who: String = "path " + d.path_id if d.is_path() else "main run"
		assert_eq(d.errors, [], who + " loads without errors")
		var mix: Dictionary = d.cfg["mix"]
		for k in ["ramp_s", "phase_fade_s", "gain_db", "dip_gain", "dip_beats", "recipe_bass_floor", "carry_bass", "bass_bus"]:
			assert_true(mix.has(k), "%s: mix.%s (a path inherits what it leaves out)" % [who, k])
		for id in d.nodes:
			var n: Dictionary = d.nodes[id]
			assert_true(n.has("family") and str(n["family"]) != "", "%s %s has a music family" % [who, id])
			var bb: Dictionary = n.get("bass_bus", {})
			for k in RunData.BASS_BUS_DEFAULT:
				assert_true(bb.has(k), "%s %s: bass_bus.%s resolved" % [who, id, k])
			assert_true(float(bb.get("drive", 0.0)) >= 0.0 and float(bb.get("drive", 0.0)) <= 0.95, "%s %s: drive in range" % [who, id])


func test_the_bass_is_in_from_the_reveal_block_on_in_every_scene_of_every_pack() -> void:
	for dv in _runs():
		var d: RunData = dv
		var who: String = "path " + d.path_id if d.is_path() else "main run"
		var st: Array = d.cfg["stages"]
		assert_eq(float(st[0]["gains"]["bass"]), 0.0, who + ": drums alone first (the reveal is the gameplay)")
		var floor_ := float(d.cfg["mix"].get("recipe_bass_floor", 0.0))
		for id in d.nodes:
			var secs: Array = d.nodes[id].get("sections", [])
			var recipes: Array = [1.0] if secs.is_empty() else secs.map(func(s: Dictionary) -> float: return maxf(float(s["gains"]["bass"]), floor_))
			for k in range(1, 4):
				for r in recipes:
					var g := float(st[k]["gains"]["bass"]) * float(r)
					assert_true(g >= 0.75, "%s %s: the bass is in at stage %d (gain %.2f, never stripped back under 0.75)" % [who, id, k, g])
		assert_true(float(d.cfg["mix"]["bass_bus"].get("drive", 0.0)) > 0.0 or not bool(d.cfg["mix"]["bass_bus"].get("enabled", false)), who + ": an enabled bass bus saturates")


func test_the_buses_run_through_runmix_and_the_bass_through_its_tone_bus() -> void:
	var d := RunData.load_path("squadron", 1)
	var a := _audio(d)
	var mixi := AudioServer.get_bus_index(RunAudio.MIX_BUS)
	assert_true(mixi >= 0, "RunMix exists")
	assert_near(AudioServer.get_bus_volume_db(mixi), float(d.cfg["mix"]["gain_db"]), 1e-4, "RunMix is the path's level")
	for k in 2:
		for b in RunAudio.BUS_PAIRS[k]:
			var i := AudioServer.get_bus_index(str(b))
			assert_eq(str(AudioServer.get_bus_send(i)), RunAudio.MIX_BUS, "%s sends to RunMix" % b)
			assert_true(i > mixi, "%s is mixed before RunMix (a higher index)" % b)
		var ti := AudioServer.get_bus_index(str(RunAudio.TONE_BUSES[k]))
		assert_eq(str(AudioServer.get_bus_send(ti)), str(RunAudio.BUS_PAIRS[k][1]), "the tone bus sends to its pair's bass bus")
		assert_true(ti > AudioServer.get_bus_index(str(RunAudio.BUS_PAIRS[k][1])), "the tone bus is mixed before the bass bus")
	# C05 has its own bass bus: shelf, then the waveshaper with its own pre and post gain
	a._begin_phase(_ev(d, "air.c05", 0.0, 1), 0.0, 0.0, 0.0)
	var bb: Dictionary = d.nodes["air.c05"]["bass_bus"]
	var tone := AudioServer.get_bus_index(str(RunAudio.TONE_BUSES[1]))
	var kinds: Array = []
	var dist: AudioEffectDistortion = null
	for e in AudioServer.get_bus_effect_count(tone):
		var fx := AudioServer.get_bus_effect(tone, e)
		kinds.append(fx.get_class())
		if fx is AudioEffectDistortion:
			dist = fx
	assert_eq(kinds, ["AudioEffectLowShelfFilter", "AudioEffectDistortion"], "no high-pass for Squadron (the sub stays), a shelf and the saturation")
	assert_true(dist != null and dist.mode == AudioEffectDistortion.MODE_WAVESHAPE, "the soft waveshaper")
	if dist != null:
		assert_near(dist.drive, float(bb["drive"]), 1e-5)
		assert_near(dist.pre_gain, float(bb["pre_gain_db"]), 1e-5)
		assert_near(dist.post_gain, float(bb["gain_db"]), 1e-5)
	a._run({"t": 16.0 * a.beat_s, "kind": "mix", "gains": d.cfg["stages"][1]["gains"]}, 0.0, 0.0)
	a._run({"t": 16.0 * a.beat_s, "kind": "reveal"}, 0.0, 0.0)
	var g: Dictionary = a._live_group()
	assert_eq(str((g["voices"]["bass"]["player"] as AudioStreamPlayer).bus), str(RunAudio.TONE_BUSES[1]), "the bass plays into the tone bus")
	assert_eq(str((g["voices"]["other"]["player"] as AudioStreamPlayer).bus), str(RunAudio.BUS_PAIRS[1][1]), "the synth goes straight onto the bass bus (the treatment), not through the tone")
	assert_eq(str((g["voices"]["drums"]["player"] as AudioStreamPlayer).bus), str(RunAudio.BUS_PAIRS[1][0]))
	a.queue_free()


func test_a_disabled_bass_bus_leaves_the_tone_bus_empty() -> void:
	var tone := RunAudio.TONE_BUSES[0]
	var d := RunData.load_default()
	var a := _audio(d)
	RunAudio._apply_bass_bus(str(tone), {"enabled": false, "drive": 0.5, "shelf_db": 3.0})
	assert_eq(AudioServer.get_bus_effect_count(AudioServer.get_bus_index(str(tone))), 0, "enabled false = the bass straight through, as before the polish")
	a.queue_free()


func test_the_bass_carries_into_the_next_scene_of_the_same_family_only() -> void:
	var d := RunData.load_default()
	assert_eq(str(d.nodes["warehouse"]["family"]), str(d.nodes["warehouse.bar"]["family"]), "one world, one family")
	assert_true(str(d.nodes["warehouse.exit"]["family"]) != str(d.nodes["mothership"]["family"]), "another world, another family")
	var a := _audio(d)
	var cg := float(d.cfg["mix"]["carry_bass"]["gain"])
	assert_true(cg > 0.0, "the carry is on in the shipped data")
	var b := a.beat_s
	a._begin_phase(_ev(d, "warehouse", 0.0, 1), 0.0, 0.0, 0.0)
	a._run({"t": 16.0 * b, "kind": "mix", "gains": d.cfg["stages"][1]["gains"]}, 0.0, 0.0)
	a._run({"t": 16.0 * b, "kind": "reveal"}, 0.0, 0.0)
	var first: Dictionary = a._live_group()
	a._begin_phase(_ev(d, "warehouse.bar", 64.0 * b, 2), 64.0 * b, 64.0 * b, 0.0)
	assert_true(bool(first.get("carry", false)), "the floor's bass carries under the bar's drums-alone block")
	assert_near(float(first["voices"]["bass"]["target"]), cg, 1e-6, "at the carry gain")
	assert_near(float(first["voices"]["drums"]["target"]), 0.0, 1e-9, "its drums fade as before")
	assert_near(float(first["voices"]["other"]["target"]), 0.0, 1e-9, "and its synth")
	var ends: Array = a._schedule.filter(func(i: Dictionary) -> bool: return str(i["kind"]) == "carry_end")
	assert_eq(ends.size(), 1, "one carry end is scheduled")
	assert_near(float(ends[0]["t"]), (64.0 + float(d.cfg["mix"]["carry_bass"]["beats"])) * b, 1e-6, "at the end of the drums-alone block, where the bar's own bass enters")
	# a dip while it carries sinks it too, and the end of the dip brings it back to the carry gain
	a._run({"t": 66.0 * b, "kind": "dip", "on": true}, 0.0, 0.0)
	assert_near(float(first["voices"]["bass"]["target"]), cg * a.dip_gain(), 1e-6)
	a._run({"t": 70.0 * b, "kind": "dip", "on": false}, 0.0, 0.0)
	assert_near(float(first["voices"]["bass"]["target"]), cg, 1e-6)
	assert_true(not a._live_group().is_empty() and a._live_group()["node"] == "warehouse.bar", "the live group is the new scene's, not the carried one")
	a._run({"t": 80.0 * b, "kind": "carry_end"}, 0.0, 0.0)
	assert_false(bool(first.get("carry", false)))
	assert_near(float(first["voices"]["bass"]["target"]), 0.0, 1e-9, "the carried bass fades out")
	a.queue_free()


func test_no_carry_across_a_world_change_or_before_a_reveal() -> void:
	var d := RunData.load_default()
	var a := _audio(d)
	var b := a.beat_s
	a._begin_phase(_ev(d, "warehouse.exit", 0.0, 1), 0.0, 0.0, 0.0)
	a._run({"t": 16.0 * b, "kind": "reveal"}, 0.0, 0.0)
	var first: Dictionary = a._live_group()
	a._begin_phase(_ev(d, "mothership", 64.0 * b, 2), 64.0 * b, 64.0 * b, 0.0)
	assert_false(bool(first.get("carry", false)), "another family: no carry, the bass fades with the rest")
	assert_near(float(first["voices"]["bass"]["target"]), 0.0, 1e-9)
	var second: Dictionary = a._live_group()
	a._begin_phase(_ev(d, "mothership.gallery", 128.0 * b, 3), 128.0 * b, 128.0 * b, 0.0)
	assert_false(bool(second.get("carry", false)), "a phase whose bass never entered has nothing to carry")
	a.queue_free()


func test_a_path_mix_overrides_the_main_run_key_by_key() -> void:
	var base := {"gain_db": 2.0, "dip_gain": 0.5, "bass_bus": {"enabled": true, "drive": 0.6, "shelf_db": 2.0}}
	var m := RunData.merge_mix(base, {"gain_db": -1.0, "bass_bus": {"drive": 0.4}})
	assert_near(float(m["gain_db"]), -1.0, 1e-9)
	assert_near(float(m["dip_gain"]), 0.5, 1e-9, "a key the path leaves out is the main run's")
	assert_near(float(m["bass_bus"]["drive"]), 0.4, 1e-9)
	assert_near(float(m["bass_bus"]["shelf_db"]), 2.0, 1e-9, "merged one level deeper")
	assert_true(bool(m["bass_bus"]["enabled"]))
	assert_near(float(base["bass_bus"]["drive"]), 0.6, 1e-9, "the main run's own mix is not touched")
