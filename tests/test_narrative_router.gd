extends TestCase
## QuestRouter: the Destination it builds, the pending change it holds, and the transaction rule (the committed route state changes only on `switched`,
## from the scene really entered), driven through MockTransitionDirector. The Rig class here is shared with the other narrative tests.

const GraphTest := preload("res://tests/test_narrative_graph.gd")


## A router wired to a mock director and an in-memory store, with helpers to play requests through the port.
class Rig:
	var graph: NarrativeGraph
	var store := NarrativeMemoryStore.new()
	var router: QuestRouter
	var mock: MockTransitionDirector
	var flags: Dictionary = {}
	var requests: Array = []  # every Destination asked for, in order
	var closed: Array = []  # [id, reason]
	var landed_log: Array = []  # [id, landed]
	var commit_results: Array = []
	var switched_n := 0
	var deferred_n := 0
	var mid_snaps: Array = []  # the committed snapshot at every locked / deferred / acknowledged signal
	var _flags_of: Dictionary = {}  # request id -> {dest id: flags_set}

	func _init(g: NarrativeGraph, laps: int = 2) -> void:
		graph = g
		router = QuestRouter.new(g, store)
		router.run_flags = flags
		router.start_run()
		mock = MockTransitionDirector.new(174.0, laps, 1)
		mock.request_closed.connect(_on_closed)
		mock.switched.connect(_on_switched)
		mock.deferred.connect(_on_deferred)
		mock.locked.connect(_on_locked)
		mock.request_acknowledged.connect(_on_ack)
		mock.set_default(router.default_destination())

	func _on_closed(id: int, reason: StringName) -> void:
		closed.append([id, reason])
		router.discard(id)

	func _on_deferred(id: int, _nb: float, _reason: StringName) -> void:
		deferred_n += 1
		mid_snaps.append(router.state.snapshot())
		router.on_deferred(id)

	func _on_locked(_id: int, _dest: Dictionary, _b: float, _plan: Dictionary) -> void:
		mid_snaps.append(router.state.snapshot())

	func _on_ack(_id: int, _ok: bool, _reason: StringName) -> void:
		mid_snaps.append(router.state.snapshot())

	func _on_switched(id: int, landed: Dictionary, _t: float) -> void:
		switched_n += 1
		landed_log.append([id, landed])
		var res := router.commit(id, landed)
		commit_results.append(res)
		for f in res["restore_flags"]:
			flags[f] = true
		var fs: Dictionary = _flags_of.get(id, {})
		if not bool(landed.get("fallback", false)) and fs.has(str(landed["id"])):
			for f in fs[str(landed["id"])]:
				flags[f] = true
		mock.set_default(router.default_destination())

	func scene() -> String:
		return router.state.current_scene()

	func snap() -> String:
		return router.state.snapshot()

	## Taps an object of the current scene: builds the destination, asks the port, holds the change. Returns the request id (0 if refused).
	func tap(object_id: String) -> int:
		var dest := router.destination_for(object_id)
		if dest.is_empty():
			return 0
		requests.append(dest.duplicate(true))
		var id := router.submit(mock, object_id)
		if id > 0:
			var fs := {}
			for e in graph.edges_from(scene()):
				if e["via"] == object_id and not (e["condition"] as Dictionary).has("auto"):
					var o := str((e["condition"] as Dictionary).get("outcome", ""))
					if o != "test_fail" and o != "fight_lost":
						fs[str(e["to"])] = (e["condition"] as Dictionary).get("flags_set", [])
			_flags_of[id] = fs
		return id

	## Advances the virtual clock boundary by boundary until nothing is pending in the router and the port has nothing locked.
	func settle(max_iter: int = 12) -> void:
		var i := 0
		while i < max_iter:
			i += 1
			var st := mock.state()
			if router.state.pending.is_empty() and st != TransitionPort.State.PENDING and st != TransitionPort.State.LOCKED:
				break
			mock.advance(maxf(mock.next_boundary_t() - mock.song_time(), 0.0) + 0.01)

	## tap + settle. True when the scene changed.
	func go(object_id: String) -> bool:
		var n := switched_n
		var id := tap(object_id)
		if id == 0:
			return false
		settle()
		return switched_n > n

	## Lets the scene's default lock and switch (nothing tapped). True when the scene changed.
	func play_default(max_iter: int = 12) -> bool:
		var n := switched_n
		var i := 0
		while i < max_iter and switched_n == n:
			i += 1
			mock.advance(maxf(mock.next_boundary_t() - mock.song_time(), 0.0) + 0.01)
		return switched_n > n

	## Puts the route state on a scene at once (a test set-up, like the Python tool's teleport): no quest, history [scene].
	func teleport(scene_id: String) -> void:
		var s := router.state.copy()
		s.location = graph.location_of(scene_id)
		s.quest = ""
		s.entry_origin = ""
		s.checkpoint = ""
		s.history = [scene_id]
		router.state.adopt(s)
		mock.set_default(router.default_destination())

	func errors() -> Array:
		return router.state.invariant_errors(graph)


static func rig() -> Rig:
	return Rig.new(GraphTest.graph())


func test_destination_of_a_scene_route() -> void:
	var r := rig()
	var d := r.router.destination_for("warehouse.exit_bar")
	assert_eq(d["id"], "main/warehouse.bar")
	assert_eq(d["path"], "main")
	assert_eq(d["node"], "warehouse.bar")
	assert_eq(d["kind"], &"scene")
	assert_eq(d["quest"], "")
	assert_eq(d.get("when"), &"lap_end")
	assert_false(d.has("fallback"), "only the director sets fallback")
	assert_eq(r.router.destination_for("no.such.object"), {})
	assert_eq(r.router.last_refusal, &"no_such_object")


func test_a_miss_twin_becomes_on_miss() -> void:
	var r := rig()
	r.teleport("main/warehouse.exit")
	var found := false
	for o in r.router.options():
		var d := r.router.destination_for(o["object"])
		if d.has("on_miss"):
			found = true
			var m: Dictionary = d["on_miss"]
			assert_true(m["id"] != d["id"], "a miss twin that leads where the success leads is left out")
			assert_false(m.has("on_miss"), "no second-level on_miss")
			for k in ["id", "path", "node", "kind"]:
				assert_true(m.has(k), "on_miss has %s" % k)
	assert_true(found, "the Door has a destination for a missed last block")


func test_quest_entries_and_returns_never_carry_on_miss() -> void:
	var g := GraphTest.graph()
	var r := rig()
	for loc in g.location_ids():
		r.teleport(g.hub_of_location(loc))
		for o in r.router.options():
			var d := r.router.destination_for(o["object"])
			if d.is_empty():
				continue
			if d["kind"] == &"quest_entry":
				assert_false(d.has("on_miss"), "%s: an entry is not gated by rhythm" % o["object"])
				assert_eq(d["quest"], g.quest_of(d["id"]))
				assert_eq(d["id"], g.entry_of(d["quest"]), "a first entry lands on the quest's entry")
	# a return
	r.teleport(g.hub_of_location("hospital_ward"))
	assert_true(r.go("hospital.enter_ember"))
	var d2 := r.router.destination_for("ember.return")
	assert_eq(d2["kind"], &"quest_return")
	assert_eq(d2["id"], "main/hospital")
	assert_eq(d2["quest"], "ember")
	assert_false(d2.has("on_miss"))


func test_the_wizard_is_outside_the_port() -> void:
	var r := rig()
	assert_true(r.router.is_legacy_object("warehouse.wizard"))
	assert_false(r.router.is_legacy_object("warehouse.enter_bassment"))
	assert_eq(r.router.destination_for("warehouse.wizard"), {})
	assert_eq(r.router.last_refusal, &"legacy")
	var res := r.router.commit_legacy("warehouse.wizard")
	assert_true(res["applied"])
	assert_eq(res["entered"], "bassment")
	assert_eq(r.scene(), "bassment/1")
	assert_eq(r.router.state.quest, "bassment")
	assert_eq(r.router.state.entry_origin, "main/warehouse")
	assert_eq(r.router.state.checkpoint, "main/warehouse")
	assert_eq(r.errors(), [])
	assert_eq(r.router.commit_legacy("warehouse.enter_bassment")["applied"], false)


func test_nothing_changes_until_switched() -> void:
	var r := rig()
	var before := r.snap()
	var saves := r.store.saves
	var id := r.tap("warehouse.enter_gospel")
	assert_true(id > 0)
	assert_false(r.router.state.pending.is_empty(), "the change is held against the request id")
	assert_eq(int(r.router.state.pending["id"]), id)
	assert_eq(r.snap(), before, "acknowledged: committed state unchanged")
	r.mock.advance(r.mock.lock_t(r.mock.next_boundary_t()) - r.mock.song_time() + 0.01)
	assert_eq(r.mock.state(), TransitionPort.State.LOCKED)
	assert_eq(r.snap(), before, "locked: committed state unchanged")
	assert_eq(r.store.saves, saves, "nothing saved before the switch")
	r.settle()
	assert_eq(r.switched_n, 1)
	assert_eq(r.scene(), "gospel/jordan")
	assert_eq(r.router.state.quest, "gospel")
	assert_true(r.store.saves > saves, "saved on switched")
	assert_true(r.router.state.pending.is_empty())
	assert_eq(r.store.saved, r.router.state.to_dict(), "what was saved is the committed state")
	for s in r.mid_snaps:
		assert_eq(s, before, "every signal before the switch saw the old state")


func test_replace_keeps_only_the_new_change() -> void:
	var r := rig()
	var before := r.snap()
	var a := r.tap("warehouse.enter_gospel")
	var b := r.tap("warehouse.enter_squadron")
	assert_true(b > a)
	assert_eq(r.closed.size(), 1)
	assert_eq(r.closed[0], [a, &"replaced"])
	assert_eq(int(r.router.state.pending["id"]), b)
	assert_eq(r.snap(), before)
	r.settle()
	assert_eq(r.scene(), "squadron/base")
	assert_eq(r.router.state.quest, "squadron")
	assert_eq(r.router.state.progress_of("gospel")["visits"], 0, "the replaced request left no trace")


func test_cancel_before_the_lock_discards_the_change() -> void:
	var r := rig()
	var before := r.snap()
	var id := r.tap("warehouse.enter_ember")
	assert_true(r.mock.cancel(id))
	assert_eq(r.closed[0], [id, &"cancelled"])
	assert_true(r.router.state.pending.is_empty())
	assert_eq(r.snap(), before)
	# the scene's default applies on the final lap, and then the state does change
	assert_true(r.play_default())
	assert_eq(r.scene(), "main/warehouse.bar", "the Floor's default exit")
	assert_eq(r.errors(), [])


func test_cancel_after_the_lock_is_refused() -> void:
	var r := rig()
	var id := r.tap("warehouse.enter_gospel")
	r.mock.advance(r.mock.lock_t(r.mock.next_boundary_t()) - r.mock.song_time() + 0.01)
	assert_false(r.mock.cancel(id))
	assert_eq(r.tap("warehouse.enter_ember"), 0, "no request while locked")
	assert_false(r.router.state.pending.is_empty(), "the held change survives the refused calls")
	r.settle()
	assert_eq(r.scene(), "gospel/jordan")


func test_unavailable_destination_leaves_the_state_alone() -> void:
	var r := rig()
	var before := r.snap()
	r.mock.fail_load_ids.assign(["gospel/jordan"])
	var id := r.tap("warehouse.enter_gospel")
	assert_true(id > 0)
	r.mock.advance(0.0)
	assert_eq(r.closed[0], [id, &"unavailable"])
	assert_true(r.router.state.pending.is_empty())
	assert_eq(r.snap(), before)
	r.mock.fail_load_ids.assign([])
	assert_true(r.go("warehouse.enter_gospel"), "the next request works")


func test_deferred_keeps_the_pending_change() -> void:
	var r := rig()
	var before := r.snap()
	r.mock.not_ready_ids.assign(["gospel/jordan"])
	var id := r.tap("warehouse.enter_gospel")
	r.mock.advance(r.mock.lock_t(r.mock.next_boundary_t()) - r.mock.song_time() + 0.01)
	assert_eq(r.deferred_n, 1, "deferred once")
	assert_eq(int(r.router.state.pending["id"]), id, "the change stays held")
	assert_eq(r.snap(), before)
	r.settle()
	assert_eq(r.scene(), "gospel/jordan")
	assert_eq(r.router.state.quest, "gospel")
	assert_eq(r.router.state.progress_of("gospel")["visits"], 1, "applied once")


func test_fallback_after_the_lock_recomputes_the_change() -> void:
	var r := rig()
	# asked for the Jesus entrance; the destination failed after the lock and the player landed in the Bar
	r.mock.fail_after_lock_ids.assign(["gospel/jordan"])
	r.mock.fallback_dest = {"id": "main/warehouse.bar", "path": "main", "node": "warehouse.bar", "kind": &"scene", "quest": ""}
	assert_true(r.go("warehouse.enter_gospel"))
	assert_true(bool(r.landed_log[0][1]["fallback"]))
	assert_eq(r.scene(), "main/warehouse.bar")
	assert_eq(r.router.state.quest, "", "no quest was entered: the saved state describes where the player really is")
	assert_eq(r.router.state.progress_of("gospel")["visits"], 0)
	assert_true(bool(r.commit_results[0]["recomputed"]))
	assert_eq(r.errors(), [])
	# a fallback into a quest scene from the mainline is an entry from the scene the player was in
	var r2 := rig()
	r2.mock.fail_after_lock_ids.assign(["main/warehouse.bar"])
	r2.mock.fallback_dest = {"id": "squadron/base", "path": "squadron", "node": "base", "kind": &"scene", "quest": ""}
	assert_true(r2.go("warehouse.exit_bar"))
	assert_eq(r2.scene(), "squadron/base")
	assert_eq(r2.router.state.quest, "squadron")
	assert_eq(r2.router.state.entry_origin, "main/warehouse")
	assert_eq(r2.router.state.checkpoint, "main/warehouse")
	assert_eq(r2.errors(), [])
	# a fallback onto a scene the graph does not know changes nothing and says so
	var r3 := rig()
	var before := r3.snap()
	r3.mock.fail_after_lock_ids.assign(["main/warehouse.bar"])
	assert_true(r3.go("warehouse.exit_bar"))
	assert_eq(r3.snap(), before)
	assert_true(r3.router.errors.size() > 0)
	assert_contains(r3.router.errors, "not in the narrative graph")


func test_on_miss_is_taken_when_the_last_block_is_missed() -> void:
	var r := rig()
	r.teleport("main/warehouse.exit")
	var door := ""
	for o in r.router.options():
		if r.router.destination_for(o["object"]).has("on_miss"):
			door = o["object"]
	assert_true(door != "")
	var d := r.router.destination_for(door)
	r.mock.miss_last_block = true
	assert_true(r.go(door))
	assert_eq(r.scene(), d["on_miss"]["id"])
	assert_eq(r.errors(), [])
	var r2 := rig()
	r2.teleport("main/warehouse.exit")
	assert_true(r2.go(door))
	assert_eq(r2.scene(), d["id"])


func test_default_destination_and_its_lock() -> void:
	var r := rig()
	var d := r.router.default_destination()
	assert_eq(d["id"], "main/warehouse.bar")
	assert_eq(d["kind"], &"scene")
	assert_true(r.play_default())
	assert_eq(r.scene(), "main/warehouse.bar")
	assert_eq(r.router.state.history, ["main/warehouse", "main/warehouse.bar"])
	assert_eq(r.errors(), [])
	# a quest scene's default is onward, never the return
	r.teleport("main/warehouse")
	assert_true(r.go("warehouse.enter_gospel"))
	var dq := r.router.default_destination()
	assert_true(dq.is_empty() or dq["kind"] == &"scene")


func test_attach_wires_the_signals() -> void:
	var g := GraphTest.graph()
	var router := QuestRouter.new(g, NarrativeMemoryStore.new())
	var mock := MockTransitionDirector.new(174.0, 2, 1)
	router.attach(mock)
	var id := router.submit(mock, "warehouse.enter_squadron")
	assert_true(id > 0)
	var other := router.submit(mock, "warehouse.enter_ember")
	assert_true(router.state.pending["id"] == other, "the replaced request's change was dropped by request_closed")
	mock.advance(mock.next_boundary_t() - mock.song_time() + 0.01)
	assert_eq(router.state.current_scene(), "ember/hollow")
	assert_false(mock.log.filter(func(x): return x["signal"] == &"switched").is_empty())
	router.detach()


func test_back_goes_to_the_previous_scene_and_return_to_the_checkpoint() -> void:
	var r := rig()
	assert_true(r.go("warehouse.enter_gospel"))
	var first := r.scene()
	var opts: Array = r.router.options()
	var onward := ""
	for o in opts:
		if o["kind"] == "scene" and not str(o["object"]).ends_with(".back") and not str(o["object"]).ends_with(".return"):
			onward = o["object"]
			break
	assert_true(onward != "")
	assert_true(r.go(onward))
	var second := r.scene()
	assert_true(second != first)
	var d := r.router.destination_for("gospel.back")
	assert_eq(d["id"], first, "back leads to the scene before this one in the history")
	assert_true(r.go("gospel.back"))
	assert_eq(r.scene(), first)
	assert_eq(r.router.state.quest, "gospel", "back stays inside the quest")
	assert_true(r.go("gospel.return"))
	assert_eq(r.scene(), "main/warehouse")
	assert_eq(r.errors(), [])
