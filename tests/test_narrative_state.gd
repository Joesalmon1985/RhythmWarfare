extends TestCase
## RouteState and the router's saving: the fields, the save format (the versioned `narrative` key), an old save without it, a newer version, damaged
## values, a save written in the middle of a quest, the history bound, and a completed quest's restart. Nothing here touches the player's real save:
## the store is NarrativeMemoryStore.

const GraphTest := preload("res://tests/test_narrative_graph.gd")
const RouterTest := preload("res://tests/test_narrative_router.gd")


func test_a_new_state_is_empty_on_the_start_scene() -> void:
	var r := RouterTest.rig()
	var s := r.router.state
	assert_eq(s.location, "warehouse_rave")
	assert_eq(s.quest, "")
	assert_eq(s.entry_origin, "")
	assert_eq(s.checkpoint, "")
	assert_eq(s.history, ["main/warehouse"])
	assert_eq(s.quest_progress.size(), 0)
	assert_eq(s.progress_of("gospel"), {"scene": "", "completed": false, "visits": 0}, "a quest never entered reads as an empty progress")
	assert_eq(s.invariant_errors(GraphTest.graph()), [])
	assert_eq(r.store.saves, 1, "start_run saves")


func test_to_dict_is_the_documented_format_and_leaves_pending_out() -> void:
	var r := RouterTest.rig()
	assert_true(r.go("warehouse.enter_bassment"))
	assert_true(r.go("trial.1.0"))
	var d := r.router.state.to_dict()
	assert_eq(int(d["version"]), 1)
	for k in ["location", "quest", "entry_origin", "checkpoint", "quest_progress", "history"]:
		assert_true(d.has(k), "has %s" % k)
	assert_false(d.has("pending"), "pending lives in memory only")
	assert_eq(d["quest"], "bassment")
	assert_eq(d["entry_origin"], "main/warehouse")
	assert_eq(d["checkpoint"], "main/warehouse")
	assert_eq(d["quest_progress"]["bassment"]["scene"], "bassment/3")
	assert_eq(int(d["quest_progress"]["bassment"]["visits"]), 1)
	assert_true(r.go("bassment.return"))
	var d2 := r.router.state.to_dict()
	assert_eq(d2["quest"], "")
	assert_true(d2["quest_progress"]["bassment"].has("items"), "the Bassment saves items, not flags")
	assert_false(d2["quest_progress"]["bassment"].has("flags"))
	# it is plain JSON
	assert_eq(JSON.parse_string(JSON.stringify(d)).size(), d.size())


func test_save_round_trip() -> void:
	var r := RouterTest.rig()
	r.flags["ember_no_vial"] = true
	assert_true(r.go("warehouse.enter_ember"))
	assert_true(r.go("ember.return"))
	assert_true(r.go("warehouse.enter_gospel"))
	var before := r.router.state.snapshot()
	var raw := JSON.stringify(r.store.saved)  # through text, as the save file would carry it
	var s2 := RouteState.from_dict(JSON.parse_string(raw), "main/warehouse")
	# the player quit inside the Jesus quest: it is closed on load, everything else is as it was
	assert_true(s2.closed_on_load)
	assert_eq(s2.quest, "")
	assert_eq(s2.progress_of("ember")["visits"], 1)
	assert_eq(s2.progress_of("gospel")["visits"], 1)
	assert_true((s2.progress_of("ember")["flags"] as Array).has("ember_no_vial"), "the quest's flags are saved when it is left")
	# a state outside any quest round-trips byte for byte
	assert_true(r.go("gospel.return"))
	before = r.router.state.snapshot()
	var s3 := RouteState.from_dict(JSON.parse_string(JSON.stringify(r.store.saved)), "main/warehouse")
	assert_eq(s3.snapshot(), before)
	assert_eq(s3.invariant_errors(GraphTest.graph()), [])


func test_load_through_the_router_and_store() -> void:
	var g := GraphTest.graph()
	var r := RouterTest.rig()
	assert_true(r.go("warehouse.enter_squadron"))
	assert_true(r.go("squadron.return"))
	var saved := r.store.saved.duplicate(true)
	var store2 := NarrativeMemoryStore.new()
	store2.saved = saved
	var router2 := QuestRouter.new(g, store2)
	var s := router2.load_state()
	assert_eq(s.snapshot(), r.router.state.snapshot())
	assert_eq(router2.errors, [])
	assert_eq(store2.saves, 0, "loading does not write")


func test_an_old_save_without_the_narrative_key_loads_the_default() -> void:
	var g := GraphTest.graph()
	var router := QuestRouter.new(g, NarrativeMemoryStore.new())
	var s := router.load_state({"paths": {}})
	assert_eq(s.location, "warehouse_rave")
	assert_eq(s.history, ["main/warehouse"])
	assert_eq(s.quest_progress.size(), 0)
	# migration: a quest whose path already has endings starts as completed
	var s2 := router.load_state({"paths": {"gospel": {"reached": ["jordan"], "endings": ["tomb"]}, "ember": {"endings": []}}})
	assert_true(bool(s2.progress_of("gospel")["completed"]))
	assert_false(bool(s2.progress_of("ember")["completed"]))
	assert_false(bool(s2.progress_of("squadron")["completed"]))
	# and the first entry into that completed quest restarts at its first scene
	router.run_flags = {}
	var dest := router.destination_for("warehouse.enter_gospel")
	assert_eq(dest["id"], "gospel/jordan")
	# a store that holds nothing, and garbage
	for junk in [null, 5, "text", [], {"version": "x"}, {"history": 3, "quest_progress": "no", "location": 7}]:
		var s3 := RouteState.from_dict(junk, "main/warehouse")
		assert_eq(s3.invariant_errors(g).size() <= 1, true, "junk %s does not crash" % str(junk))


func test_a_newer_version_is_ignored_and_not_overwritten() -> void:
	var g := GraphTest.graph()
	var store := NarrativeMemoryStore.new()
	store.saved = {"version": 99, "location": "hell", "somethingnew": [1, 2, 3]}
	var router := QuestRouter.new(g, store)
	var s := router.load_state()
	assert_true(s.newer_than_known)
	assert_eq(s.location, "warehouse_rave", "the newer value is ignored")
	var before := store.saved.duplicate(true)
	var mock := MockTransitionDirector.new(174.0, 2, 1)
	router.attach(mock)
	assert_true(router.submit(mock, "warehouse.enter_gospel") > 0)
	mock.advance(mock.next_boundary_t() - mock.song_time() + 0.01)
	assert_eq(router.state.current_scene(), "gospel/jordan", "play goes on")
	assert_eq(store.saved, before, "the newer value is not overwritten")
	assert_eq(store.saves, 0)


func test_a_save_written_inside_a_quest_is_closed_on_load() -> void:
	var g := GraphTest.graph()
	var r := RouterTest.rig()
	assert_true(r.go("warehouse.enter_gospel"))
	var onward := ""
	for o in r.router.options():
		if o["kind"] == "scene" and not str(o["object"]).ends_with(".back") and not str(o["object"]).ends_with(".return"):
			onward = o["object"]
			break
	assert_true(r.go(onward))
	var in_quest := r.scene()
	assert_eq(r.router.state.quest, "gospel")
	var store2 := NarrativeMemoryStore.new()
	store2.saved = r.store.saved.duplicate(true)
	var router2 := QuestRouter.new(g, store2)
	var s := router2.load_state()
	assert_true(s.closed_on_load)
	assert_eq(s.quest, "")
	assert_eq(s.entry_origin, "")
	assert_eq(s.checkpoint, "")
	assert_eq(s.current_scene(), "main/warehouse", "the player starts on the checkpoint hub")
	assert_eq(s.progress_of("gospel")["scene"], in_quest, "all progress is kept")
	assert_eq(s.invariant_errors(g), [])
	# and entering again resumes where the player was
	var d := router2.destination_for("warehouse.enter_gospel")
	assert_eq(d["id"], in_quest)


func test_an_inconsistent_save_is_repaired_with_a_sentence() -> void:
	var g := GraphTest.graph()
	var store := NarrativeMemoryStore.new()
	store.saved = {"version": 1, "location": "hell", "quest": "", "entry_origin": "", "checkpoint": "",
		"quest_progress": {"gospel": {"scene": "ember/hollow", "completed": true, "visits": 4}, "ghost": {"scene": "x", "completed": false, "visits": 1}},
		"history": ["main/no_such_scene"]}
	var router := QuestRouter.new(g, store)
	var s := router.load_state()
	assert_eq(router.errors.size(), 1)
	assert_contains(router.errors, "repaired")
	assert_eq(s.invariant_errors(g), [])
	assert_eq(s.current_scene(), "main/warehouse")
	assert_eq(s.progress_of("gospel")["scene"], "", "a saved scene of another quest is dropped")
	assert_true(bool(s.progress_of("gospel")["completed"]), "but what was completed stays")
	assert_false(s.quest_progress.has("ghost"))


func test_history_is_bounded() -> void:
	var g := GraphTest.graph()
	var r := RouterTest.rig()
	assert_eq(r.router.state.history_limit, 32)
	for i in 40:
		assert_true(r.go("warehouse.enter_gospel"))
		assert_true(r.go("gospel.return"))
	var h := r.router.state.history
	assert_eq(h.size(), 32)
	assert_eq(h.back(), "main/warehouse")
	assert_eq(r.router.state.invariant_errors(g), [])
	var s := RouteState.new()
	s.history_limit = 8
	for i in 20:
		s.push_history("main/warehouse")
	assert_eq(s.history.size(), 8)


func test_a_completed_quest_restarts_and_keeps_completed() -> void:
	var g := GraphTest.graph()
	for qid in ["gospel", "squadron", "ember", "bassment"]:
		var r := RouterTest.rig()
		var hub := "main/warehouse"
		var ends: Array = []
		for q in g.quests:
			if q["id"] == qid:
				ends = q["completion"]
		# reach an ending: teleport the quest state to the ending scene (the walk there is in test_narrative_routes)
		assert_true(r.go("warehouse.enter_" + qid), qid)
		var s := r.router.state.copy()
		var prog := s.progress_for_write(qid)
		prog["scene"] = ends[0]
		prog["completed"] = true
		s.history.append(ends[0])
		r.router.state.adopt(s)
		assert_true(r.go(qid + ".return"), qid)
		assert_eq(r.scene(), hub)
		assert_true(bool(r.router.state.progress_of(qid)["completed"]), "%s: completed is kept on leaving" % qid)
		assert_eq(r.router.state.progress_of(qid)["scene"], ends[0])
		var visits := int(r.router.state.progress_of(qid)["visits"])
		assert_true(r.go("warehouse.enter_" + qid), qid)
		assert_eq(r.scene(), g.entry_of(qid), "%s: a completed quest restarts at its first scene" % qid)
		assert_true(bool(r.router.state.progress_of(qid)["completed"]), "%s: and keeps completed" % qid)
		assert_eq(int(r.router.state.progress_of(qid)["visits"]), visits + 1)
		assert_eq(r.errors(), [])


func test_landing_on_a_completion_scene_completes_the_quest() -> void:
	var g := GraphTest.graph()
	var r := RouterTest.rig()
	assert_true(r.go("warehouse.enter_gospel"))
	var ending := "gospel/jerusalem.tomb"
	assert_true(g.is_completion(ending))
	assert_false(bool(r.router.state.progress_of("gospel")["completed"]))
	# the director says where the player really is (a landing the router did not ask for): the quest is completed
	assert_true(r.router.commit(0, {"id": ending})["applied"])
	assert_eq(r.scene(), ending)
	assert_true(bool(r.router.state.progress_of("gospel")["completed"]))
	assert_eq(r.errors(), [])


func test_quest_flags_are_saved_on_leaving_and_restored_on_entering() -> void:
	var r := RouterTest.rig()
	assert_true(r.go("warehouse.enter_ember"))
	r.flags["ember_no_vial"] = true
	r.flags["gospel_x"] = true  # another quest's flag is not saved with this one
	assert_true(r.go("ember.return"))
	var saved: Array = r.router.state.progress_of("ember")["flags"]
	assert_eq(saved, ["ember_no_vial"])
	r.flags.clear()
	assert_true(r.go("warehouse.enter_ember"))
	assert_true(r.flags.has("ember_no_vial"), "restored by the commit result")
	# the Bassment's items
	r.flags["item:lamp"] = true
	assert_true(r.go("ember.return"))
	assert_true(r.go("warehouse.enter_bassment"))
	r.flags["item:lamp"] = true
	assert_true(r.go("bassment.return"))
	assert_eq(r.router.state.progress_of("bassment")["items"], ["lamp"])
	r.flags.clear()
	assert_true(r.go("warehouse.enter_bassment"))
	assert_true(r.flags.has("item:lamp"), "carried items come back")


func test_a_failed_save_keeps_the_state_in_memory() -> void:
	var r := RouterTest.rig()
	r.store.fail_next = true
	assert_true(r.go("warehouse.enter_gospel"))
	assert_eq(r.scene(), "gospel/jordan")
	assert_eq(r.router.save_failures, 1)
	assert_false(bool(r.commit_results[0]["saved"]))
	assert_true(r.go("gospel.return"))
	assert_eq(r.store.saved, r.router.state.to_dict(), "the next save writes everything")
