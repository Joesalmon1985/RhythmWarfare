extends TestCase
## The failure paths of the transition engine (stage M2.4, docs/parallel-development/MUSIC_TRANSITIONS.md section 8) through the whole engine on fixture packs
## (tests/fixtures/transition/blend_rig.gd): no sidecar or an invalid one (the pack's values), no drop at all (cut, fallback), an unready pack (the single `not_ready` deferral, then `cut` with
## fallback and an ordinary scene), the Bassment taking the run during a blend, a path hand-off (always `cut`), and memory (the tail freed at its floor, the pins let go at the switch).

const Rig := preload("res://tests/fixtures/transition/blend_rig.gd")


func _rig(bpms: Array, extra := {}) -> RefCounted:
	var chain: Array = []
	for i in bpms.size():
		var c := {"track": "fb_%d" % i, "spec": Rig.spec(float(bpms[i]))}
		c.merge(extra.get(i, {}), true)
		chain.append(c)
	return Rig.new(tree, chain, 1)


func _dest(node: String) -> Dictionary:
	return {"id": "main/" + node, "path": "main", "node": node, "kind": &"scene", "quest": "", "when": &"lap_end"}


func test_a_missing_or_invalid_sidecar_plans_from_the_pack() -> void:
	var rig := _rig([174.0, 172.0])
	var p: Dictionary = rig.data.track_scenes.plan_of("tx1")
	assert_eq(str(p["sidecar_state"]), "missing")
	p["sidecar_state"] = "invalid"  # (TransitionSidecars.load_track gives {} for an invalid one: ignored as a whole)
	rig.run_transitions(1)
	assert_eq((rig.signals(&"locked")[0]["args"][3] as Dictionary)["mode"], &"blend", "the pack's own drop and grid")
	rig.free_all()


func test_a_track_without_a_drop_is_entered_with_a_cut() -> void:
	var rig := _rig([174.0, 172.0])
	(rig.data.track_scenes.plan_of("tx1") as Dictionary)["drop_bar"] = -1
	rig.run_transitions(1)
	var plan: Dictionary = rig.signals(&"locked")[0]["args"][3]
	assert_eq(plan["mode"], &"cut")
	assert_true(bool(plan["fallback"]), "forced by missing metadata")
	assert_eq(str(rig.director.lock_log[0]["recipe"].get("reason", "")), "missing")
	assert_eq(rig.audio.track.tail_count(), 0)
	rig.free_all()


func test_an_unready_pack_defers_once_then_cuts_into_an_ordinary_scene() -> void:
	var rig := _rig([174.0, 172.0])
	var dir: TransitionDirector = rig.director
	var real: Callable = dir.load_fn
	dir.load_fn = func(d: RunData, node: String) -> String:
		var s := str(real.call(d, node))
		return "loading" if node == "tx1" and s != "" else s  # (tx1's stems never finish loading)
	var id := dir.request(_dest("tx1"))
	assert_true(id > 0)
	rig.run_transitions(1, 400.0)
	var defs: Array = rig.signals(&"deferred")
	assert_eq(defs.size(), 1, "one deferral")
	assert_eq((defs[0]["args"] as Array)[2], &"not_ready")
	var la: Array = rig.signals(&"locked")[0]["args"]
	assert_eq(int(la[0]), id)
	assert_eq((la[3] as Dictionary)["mode"], &"cut", "then a cut")
	assert_true(bool((la[3] as Dictionary)["fallback"]))
	assert_near(float(la[2]) - float((defs[0]["args"] as Array)[1]), 0.0, 1e-6, "at the boundary the deferral named")
	assert_eq(rig.engine.node_id, "tx1")
	assert_false(rig.engine.is_track_scene(), "the scene plays as an ordinary one")
	assert_eq(rig.audio.track.log.filter(func(x: Dictionary) -> bool: return str(x["kind"]) == "prestart"), [], "no track group started for it")
	assert_eq(rig.audio.track.tail_count(), 0)
	assert_eq(rig.signals(&"completed").size(), 1)
	rig.free_all()


func test_the_bassment_taking_the_run_during_a_blend_leaves_the_tail_to_its_floor() -> void:
	var rig := _rig([174.0, 171.0])
	while rig.signals(&"switched").is_empty():
		rig.advance(0.25)
	rig.advance(1.0)
	assert_eq(rig.audio.track.tail_count(), 1, "a blend is running")
	var t: float = rig.t
	rig.director.excursion(&"armed")
	rig.director.excursion(&"enter")
	rig.audio.track.on_event({"kind": "phase_start", "t": t, "node": "trial", "phase": 99})  # (the dungeon's own music begins: no track)
	var end_t := float(rig.director.lock_log[0]["plan"]["complete_t"]) + 0.5
	while rig.t < end_t:
		rig.t += 1.0 / 60.0
		for g in rig.audio.track._groups:  # (no frames pass inside a test: the 0.6 s fades run here)
			(g["transport"] as TrackTransport)._process(1.0 / 60.0)
		rig.audio.track.step(rig.t, 0.0)
		rig.audio.check_silence(rig.t)
		rig.director.step(rig.t)
	assert_eq(rig.audio.track.tail_count(), 0, "the tail reached its floor")
	assert_eq(rig.audio.track.live(), {}, "the incoming track faded for the dungeon")
	assert_eq(rig.signals(&"completed").size(), 1, "completed still fires")
	rig.free_all()


func test_a_path_hand_off_is_always_a_cut() -> void:
	var rig := _rig([174.0, 172.0])
	var dir: TransitionDirector = rig.director
	var other := RunData.load_default()  # (another run's data: the director plans a hand-off when the destination's run is not the engine's)
	for id in rig.ids:
		other.nodes[id] = rig.data.nodes[id]
	other.track_scenes = rig.data.track_scenes
	rig.advance(1.0)
	rig.audio.track.request_scene(rig.data, "tx1")
	rig.wait_loads()
	var pl: Dictionary = dir._plan_for({"route": "x", "start": "tx1", "data": other, "node": "tx1"}, 100.0, false, true)
	assert_eq(pl["mode"], &"cut", "into another run: cut")
	var same: Dictionary = dir._plan_for({"route": "tx1", "start": "", "data": rig.data, "node": "tx1"}, 100.0, false, true)
	assert_eq(same["mode"], &"blend", "the same pair inside one run blends")
	rig.free_all()


func test_memory_the_tail_is_freed_and_the_pins_let_go() -> void:
	var rig := _rig([174.0, 171.0, 175.0])
	var dir: TransitionDirector = rig.director
	dir.request(_dest("tx1"))
	assert_false(rig.audio.track._pinned.is_empty(), "the requested destination is pinned")
	rig.run_transitions(2, 400.0)
	assert_eq(rig.audio.track.active_group_count(), 1, "after completed only the playing group is left")
	assert_eq(rig.audio.track._pinned, {}, "the pins went at the switch")
	assert_true(rig.audio.track.cached().size() <= 3, "packs held: the playing one, its routes' and what was not let go yet (%s)" % str(rig.audio.track.cached()))
	rig.free_all()
