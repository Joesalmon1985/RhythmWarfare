extends TestCase
## The Bassment's music in the run (TrialScene.begin hands RunAudio a phase_start for node "trial", which is no scene of the run's data): the dungeon's pack must start on its downbeat
## while the scene before fades. Until 6 November 2026 RunAudio read data.nodes["trial"] there (since the arrangements of 4 November), so the dungeon was entered in silence.


func _audio(d: RunData) -> RunAudio:
	var a := RunAudio.new()
	tree.root.add_child(a)
	a.configure(d)
	return a


func _trial_events(m: Dictionary, t: float, phase: int) -> Array:
	return [{"kind": "phase_start", "node": "trial", "phase": phase, "t": t, "treatment": m["treatment"], "audio": m["audio"]},
		{"kind": "mix", "t": t + 0.0001, "gains": {"drums": 1.0, "bass": 0.45, "other": 0.45}},
		{"kind": "reveal", "t": t + 0.0002}]


func test_the_dungeon_pack_starts_on_its_downbeat_and_the_warehouse_fades() -> void:
	var d := RunData.load_default()
	var tdata := TrialData.load_default()
	var m: Dictionary = tdata.raw["music"]
	assert_true(d.packs.has(str(m["audio"])), "the dungeon's pack (%s) is one of the run's packs" % str(m["audio"]))
	var a := _audio(d)
	a._begin_phase({"kind": "phase_start", "node": "warehouse", "t": 0.0, "phase": 1, "treatment": "none", "audio": d.nodes["warehouse"]["audio"]}, 0.0, 0.0, 0.0)
	assert_eq(a.active_phase_count(), 1, "the Warehouse plays")
	var t := 32.0 * a.beat_s
	for ev in _trial_events(m, t, 2):
		a.on_event(ev)
	assert_eq(a._schedule.size(), 3, "the dungeon's phase, mix and reveal are scheduled (it has no sections)")
	while not a._schedule.is_empty():
		var item: Dictionary = a._schedule.pop_front()
		a._run(item, float(item["t"]), 0.0)
	assert_eq(a.active_phase_count(), 2, "the dungeon's group starts beside the fading Warehouse")
	var g: Dictionary = a._live_group()
	assert_eq(str(g.get("pack", "")), str(m["audio"]), "the live group plays the dungeon's pack")
	assert_eq(str(g.get("node", "")), "trial")
	for v in ["drums", "bass", "other"]:
		assert_true((g.get("voices", {}) as Dictionary).has(v), "the dungeon's %s voice is playing" % v)
	assert_near(float(g["voices"]["drums"]["target"]), 1.0, 1e-9, "at the dungeon's own mix")
	assert_near(float(g["voices"]["bass"]["target"]), 0.45, 1e-9)
	var old: Dictionary = a._groups[0]
	assert_true(bool(old["fading"]), "the Warehouse group fades from the dungeon's downbeat")
	var starts: Array = a.voice_log.filter(func(v: Dictionary) -> bool: return str(v["node"]) == "trial")
	assert_eq(starts.size(), 3, "three dungeon voices logged with their start lag")
	a.stop()
	a.queue_free()
