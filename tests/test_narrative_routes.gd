extends TestCase
## Rules 9 and 10 of the narrative graph on the real classes, against MockTransitionDirector: cycles and re-entry (20 scripted cases: every quest from every hub),
## seeded random walks that include replaced, cancelled, unavailable, deferred and fallback-after-lock requests, and the three illustrative routes of
## NARRATIVE_GRAPH.md section 4 end to end.

const GraphTest := preload("res://tests/test_narrative_graph.gd")
const RouterTest := preload("res://tests/test_narrative_router.gd")
const WALKS := 300
const WALK_STEPS := 120


## ---------------------------------------------------------------- helpers

## The object of a hub that enters `quest_id` (ungated, through the port).
func _entrance(g: NarrativeGraph, hub: String, quest_id: String) -> String:
	for e in g.entrances_from(hub):
		if e["quest"] == quest_id and not e.get("legacy", false):
			return e["via"]
	return ""


## The first edge of a shortest route of scene edges inside a quest from `from` to any of `goals` (item locks ignored: the caller sets the flags), or {}.
func _quest_step(g: NarrativeGraph, from: String, goals: Array, quest_id: String) -> Dictionary:
	var first := {from: {}}
	var queue: Array = [from]
	while not queue.is_empty():
		var n: String = queue.pop_front()
		if goals.has(n):
			return first[n]
		for e in g.edges_from(n):
			var t: String = e["to"]
			var c: Dictionary = e["condition"]
			if e["kind"] != "scene" or e.get("hidden", false) or NarrativeGraph.MISS_OUTCOMES.has(c.get("outcome", "")) or c.get("previous_scene", false) \
					or first.has(t) or not g.resolves(t) or g.quest_of(t) != quest_id:
				continue
			first[t] = e if n == from else first[n]
			queue.append(t)
	return {}


## Plays the quest forward with real requests until it is on one of `goals`. Item flags the next route needs are set first (a pickup). Returns true on arrival.
func _play_to(r: RouterTest.Rig, goals: Array, quest_id: String) -> bool:
	for i in 80:
		if goals.has(r.scene()):
			return true
		var e := _quest_step(r.graph, r.scene(), goals, quest_id)
		if e.is_empty():
			return false
		for f in e["condition"]["flags_all"]:
			r.flags[f] = true
		if (e["condition"] as Dictionary).get("auto", false):
			if not r.play_default():
				return false
		elif not r.go(e["via"]):
			return false
		if not r.errors().is_empty():
			return false
	return goals.has(r.scene())


## The first route of a mainline scene to `target` (a breadth-first search over scene edges between mainline scenes, miss twins included): [edge, ...].
func _mainline_route(g: NarrativeGraph, from: String, target: String, fset: Dictionary) -> Array:
	var prev := {from: null}
	var queue: Array = [from]
	while not queue.is_empty():
		var n: String = queue.pop_front()
		if n == target:
			var path: Array = []
			var k := n
			while prev[k] != null:
				path.push_front(prev[k])
				k = prev[k]["from"]
			return path
		for e in g.edges_from(n):
			var t: String = e["to"]
			if e["kind"] != "scene" or e.get("hidden", false) or t == n or prev.has(t) or not g.is_mainline(t) or (e["condition"] as Dictionary).get("previous_scene", false):
				continue
			var ok := true
			for f in e["condition"]["flags_all"]:
				if not fset.has(f):
					ok = false
			for f in e["condition"]["flags_none"]:
				if fset.has(f):
					ok = false
			if ok:
				prev[t] = e
				queue.append(t)
	return []


## Walks the mainline to `target` by real requests (a missed last block for a miss twin). Returns true on arrival.
func _walk_to(r: RouterTest.Rig, target: String) -> bool:
	var route := _mainline_route(r.graph, r.scene(), target, NarrativeGraph.flag_set(r.flags))
	if route.is_empty() and r.scene() != target:
		return false
	for e in route:
		var miss: bool = (e["condition"] as Dictionary).get("outcome", "") == "on_miss"
		r.mock.miss_last_block = miss
		var ok: bool
		if (e["condition"] as Dictionary).get("auto", false):
			ok = r.play_default()
		else:
			ok = r.go(e["via"])
		r.mock.miss_last_block = false
		if not ok or r.scene() != e["to"] or not r.errors().is_empty():
			return false
	return r.scene() == target


## Every scene on the way offers at least three choices in the graph (the Bassment's declared exception aside).
func _check_choices(r: RouterTest.Rig, seen: Dictionary) -> void:
	var s := r.scene()
	if seen.has(s):
		return
	seen[s] = true
	if r.graph.excused_scenes().has(s):
		return
	assert_true(r.graph.choice_count(s) >= 3, "%s offers %d choices" % [s, r.graph.choice_count(s)])


func _kinds(r: RouterTest.Rig) -> Array:
	var out: Array = []
	for d in r.requests:
		out.append(d["kind"])
	return out


## ---------------------------------------------------------------- rule 9: the scripted cases

func test_scripted_cases_every_quest_from_every_hub() -> void:
	var g := GraphTest.graph()
	var cases := 0
	for loc in g.location_ids():
		var hub := g.hub_of_location(loc)
		for qid in g.quest_ids():
			cases += 1
			var tag := "%s from %s" % [qid, loc]
			var r := RouterTest.rig()
			r.teleport(hub)
			var obj := _entrance(g, hub, qid)
			assert_true(obj != "", "%s: the hub shows an entrance" % tag)
			var entry := g.entry_of(qid)
			# enter: lands on the entry, records the origin and the checkpoint
			assert_true(r.go(obj), tag)
			var s := r.router.state
			assert_eq(r.scene(), entry, tag)
			assert_eq(s.quest, qid, tag)
			assert_eq(s.entry_origin, hub, tag)
			assert_eq(s.checkpoint, hub, tag)
			assert_eq(s.location, loc, tag)
			assert_eq(int(s.progress_of(qid)["visits"]), 1, tag)
			assert_eq(r.errors(), [], tag)
			# move one scene
			var next_obj := ""
			for o in r.router.options():
				if o["kind"] == "scene" and o["to"] != r.scene() and o["to"] != NarrativeGraph.CHECKPOINT and not str(o["object"]).ends_with(".back"):
					next_obj = o["object"]
					break
			if next_obj != "":
				assert_true(r.go(next_obj), tag)
			var left := r.scene()
			assert_eq(r.errors(), [], tag)
			# return: lands on the checkpoint, the scene left is saved, the quest fields are cleared
			var ret := g.return_edge(left)
			assert_false(ret.is_empty(), "%s: a visible return in %s" % [tag, left])
			assert_true(r.go(ret["via"]), tag)
			assert_eq(r.scene(), hub, tag)
			assert_eq(s.quest, "", tag)
			assert_eq(s.entry_origin, "", tag)
			assert_eq(s.checkpoint, "", tag)
			assert_eq(s.progress_of(qid)["scene"], left, tag)
			assert_eq(r.errors(), [], tag)
			# re-enter: resumes at the start of the scene left
			assert_true(r.go(obj), tag)
			assert_eq(r.scene(), left, "%s: resumes where it was left" % tag)
			assert_eq(int(s.progress_of(qid)["visits"]), 2, tag)
			assert_eq(s.checkpoint, hub, tag)
			# play to an ending: completed
			var ends: Array = []
			for q in g.quests:
				if q["id"] == qid:
					ends = q["completion"]
			if not ends.has(r.scene()):
				assert_true(_play_to(r, ends, qid), "%s: a way to an ending from %s" % [tag, r.scene()])
			assert_true(bool(s.progress_of(qid)["completed"]), "%s: completed" % tag)
			assert_eq(r.errors(), [], tag)
			# return, re-enter: restarts at the entry and keeps completed
			assert_true(r.go(g.return_edge(r.scene())["via"]), tag)
			assert_eq(r.scene(), hub, tag)
			assert_true(r.go(obj), tag)
			assert_eq(r.scene(), entry, "%s: a completed quest restarts at its first scene" % tag)
			assert_true(bool(s.progress_of(qid)["completed"]), "%s: completed is kept" % tag)
			assert_eq(int(s.progress_of(qid)["visits"]), 3, tag)
			assert_eq(r.errors(), [], tag)
	assert_eq(cases, 20)


func test_cycles_can_be_left() -> void:
	# every quest scene can reach its return, and a cycle inside a quest (a back option, a restart) can be left by the return
	var g := GraphTest.graph()
	var r := RouterTest.rig()
	for qid in g.quest_ids():
		r.teleport("main/warehouse")
		assert_true(r.go(_entrance(g, "main/warehouse", qid)))
		for i in 5:  # forth and back, forth and back
			var fwd := ""
			for o in r.router.options():
				if o["kind"] == "scene" and o["to"] != r.scene() and not str(o["object"]).ends_with(".back"):
					fwd = o["object"]
					break
			if fwd == "":
				break
			assert_true(r.go(fwd))
			var back: String = str(qid) + ".back"
			if qid != "bassment" and r.router.destination_for(back).size() > 0:
				assert_true(r.go(back))
		assert_true(r.go(qid + ".return"))
		assert_eq(r.scene(), "main/warehouse")
		assert_eq(r.errors(), [])


## ---------------------------------------------------------------- rules 9 and 10: seeded random walks

## One walk. Returns {steps, switched, closed, fallbacks, deferrals, misses, defaults, errors: [...]}.
func _walk(seed_value: int, steps: int) -> Dictionary:
	var g := GraphTest.graph()
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var r := RouterTest.rig()
	var stats := {"steps": 0, "switched": 0, "closed": 0, "fallbacks": 0, "deferrals": 0, "misses": 0, "defaults": 0, "returns": 0, "entries": 0, "errors": []}
	var errs: Array = stats["errors"]
	var scene_ids: Array = g.nodes.keys()
	scene_ids.sort()
	for step in steps:
		var tag := "seed %d step %d at %s" % [seed_value, step, r.scene()]
		var opts: Array = []
		for o in r.router.options():
			if not o["legacy"]:
				opts.append(o)
		var before := r.snap()
		var n_sw := r.switched_n
		var n_closed := r.closed.size()
		var n_def := r.deferred_n
		var mid0 := r.mid_snaps.size()
		var cp_before := r.router.state.checkpoint
		var roll := rng.randf()
		var last_dest: Dictionary = {}
		var expect_switch := true
		if opts.is_empty() or roll > 0.94:
			# nothing tapped: the default locks on the final lap
			if r.router.default_destination().is_empty():
				if opts.is_empty():
					errs.append("%s: no option and no default" % tag)
					break
				continue
			stats["defaults"] += 1
			r.play_default()
		else:
			var o: Dictionary = opts[rng.randi() % opts.size()]
			var id := r.tap(o["object"])
			if id == 0:
				errs.append("%s: %s was an option but could not be requested (%s)" % [tag, o["object"], str(r.router.last_refusal)])
				break
			last_dest = r.requests.back()
			if r.snap() != before:
				errs.append("%s: a request changed the committed state" % tag)
			if roll < 0.12:  # changed my mind before the lock
				var cancelled := r.mock.cancel(id)
				if not cancelled or r.snap() != before or not r.router.state.pending.is_empty():
					errs.append("%s: cancel left a trace" % tag)
				expect_switch = false
			elif roll < 0.22:  # replaced by another object
				var o2: Dictionary = opts[rng.randi() % opts.size()]
				var id2 := r.tap(o2["object"])
				if id2 > 0:
					last_dest = r.requests.back()
					if r.snap() != before:
						errs.append("%s: a replace changed the committed state" % tag)
				r.settle()
			elif roll < 0.28:  # the destination cannot be loaded
				r.mock.fail_load_ids.assign([last_dest["id"]])
				r.mock.advance(0.0)
				r.mock.fail_load_ids.assign([])
				expect_switch = false
				if r.snap() != before or not r.router.state.pending.is_empty():
					errs.append("%s: unavailable left a trace" % tag)
			elif roll < 0.35:  # deferred once, then locks as a cut
				r.mock.not_ready_ids.assign([last_dest["id"]])
				r.settle()
				r.mock.not_ready_ids.assign([])
			elif roll < 0.43:  # the destination fails after the lock
				var fb: String = scene_ids[rng.randi() % scene_ids.size()]
				r.mock.fail_after_lock_ids.assign([last_dest["id"]])
				r.mock.fallback_dest = {"id": fb, "path": fb.get_slice("/", 0), "node": fb.substr(fb.find("/") + 1), "kind": &"scene", "quest": ""}
				r.settle()
				r.mock.fail_after_lock_ids.assign([])
				stats["fallbacks"] += 1
			elif roll < 0.50 and last_dest.has("on_miss"):  # the last block is missed
				r.mock.miss_last_block = true
				r.settle()
				r.mock.miss_last_block = false
				stats["misses"] += 1
			else:
				r.settle()
		# after the step
		stats["steps"] += 1
		var switched := r.switched_n > n_sw
		if not expect_switch and switched:
			errs.append("%s: a cancelled or unavailable request switched" % tag)
		if not switched:
			if r.snap() != before:
				errs.append("%s: no switched arrived, yet the committed state changed" % tag)
		else:
			stats["switched"] += 1
			var landed: Dictionary = r.landed_log.back()[1]
			if r.scene() != str(landed["id"]):
				errs.append("%s: committed scene %s differs from landed %s" % [tag, r.scene(), landed["id"]])
			if not bool(landed.get("fallback", false)) and not last_dest.is_empty():
				if last_dest["kind"] == &"quest_return" and str(landed["id"]) == last_dest["id"] and last_dest["id"] != cp_before:
					errs.append("%s: the return did not land on the checkpoint %s" % [tag, cp_before])
				if last_dest["kind"] == &"quest_return":
					stats["returns"] += 1
				elif last_dest["kind"] == &"quest_entry":
					stats["entries"] += 1
		for i in range(mid0, r.mid_snaps.size()):
			if r.mid_snaps[i] != before:
				errs.append("%s: the committed state changed before the switch" % tag)
				break
		stats["closed"] += r.closed.size() - n_closed
		stats["deferrals"] += r.deferred_n - n_def
		for e in r.errors():
			errs.append("%s: invariant: %s" % [tag, e])
		if not r.router.state.pending.is_empty():
			errs.append("%s: a pending change was left after the request ended" % tag)
		if not errs.is_empty():
			break
	for e in r.router.errors:
		errs.append("seed %d: router error: %s" % [seed_value, e])
	return stats


func test_random_walks_keep_history_and_checkpoint_consistent() -> void:
	var total := {"steps": 0, "switched": 0, "closed": 0, "fallbacks": 0, "deferrals": 0, "misses": 0, "defaults": 0, "returns": 0, "entries": 0}
	var broken := 0
	for seed_value in WALKS:
		var st := _walk(seed_value, WALK_STEPS)
		for k in total:
			total[k] += int(st[k])
		var errs: Array = st["errors"]
		assert_eq(errs.size(), 0, "walk %d: %s" % [seed_value, str(errs.slice(0, 2))])
		if not errs.is_empty():
			broken += 1
	print("random walks: %d walks, %d steps, %s" % [WALKS, int(total["steps"]), str(total)])
	assert_eq(broken, 0)
	for k in ["switched", "closed", "fallbacks", "deferrals", "misses", "defaults", "returns", "entries"]:
		assert_true(int(total[k]) > 20, "the walks exercised %s (%d)" % [k, int(total[k])])


## ---------------------------------------------------------------- the three illustrative routes

func test_route_1_warehouse_dungeon_and_back_then_hospital_jesus_and_back() -> void:
	var g := GraphTest.graph()
	var r := RouterTest.rig()
	var seen := {}
	_check_choices(r, seen)
	assert_eq(r.scene(), "main/warehouse")
	# the Dungeon from the Floor's own hatch, through the port
	assert_true(r.go("warehouse.enter_bassment"))
	assert_eq(r.requests.back()["kind"], &"quest_entry")
	assert_eq(r.scene(), "bassment/1")
	assert_eq(r.router.state.entry_origin, "main/warehouse")
	assert_eq(r.router.state.checkpoint, "main/warehouse")
	_check_choices(r, seen)
	assert_true(r.go("trial.1.0"))  # "Climb down the ladder"
	assert_eq(r.scene(), "bassment/3")
	_check_choices(r, seen)
	assert_true(r.go("bassment.return"))
	assert_eq(r.requests.back()["kind"], &"quest_return")
	assert_eq(r.scene(), "main/warehouse", "the return lands on the hub entered from")
	assert_eq(r.router.state.quest, "")
	assert_eq(r.router.state.progress_of("bassment")["scene"], "bassment/3")
	# on to the Hospital Ward
	assert_true(_walk_to(r, "main/hospital"), "a mainline route to the Hospital Ward")
	assert_eq(r.router.state.location, "hospital_ward")
	assert_true(r.router.state.history.has("main/mothership") or r.router.state.history.has("main/underworld"))
	_check_choices(r, seen)
	# Jesus from the Hospital Ward hub
	assert_true(r.go("hospital.enter_gospel"))
	assert_eq(r.requests.back()["id"], "gospel/jordan")
	assert_eq(r.requests.back()["kind"], &"quest_entry")
	assert_eq(r.router.state.checkpoint, "main/hospital")
	_check_choices(r, seen)
	assert_true(_first_onward(r))
	var left := r.scene()
	assert_true(left != "gospel/jordan")
	_check_choices(r, seen)
	assert_true(r.go("gospel.return"))
	assert_eq(r.scene(), "main/hospital")
	assert_eq(r.router.state.progress_of("gospel")["scene"], left)
	# progress is kept: the Bassment still stands at passage 3, and Jesus resumes
	assert_eq(r.router.state.progress_of("bassment")["scene"], "bassment/3")
	assert_true(r.go("hospital.enter_gospel"))
	assert_eq(r.scene(), left)
	assert_eq(int(r.router.state.progress_of("gospel")["visits"]), 2)
	assert_true(r.go("gospel.return"))
	# the state at the end is the worked example of NARRATIVE_GRAPH.md 3.3
	var d := r.store.saved
	assert_eq(d["location"], "hospital_ward")
	assert_eq(d["quest"], "")
	assert_eq(d["history"].back(), "main/hospital")
	assert_eq(d["history"].slice(0, 1), ["main/warehouse"])
	assert_true(d["quest_progress"].has("bassment") and d["quest_progress"].has("gospel"))
	assert_eq(r.errors(), [])
	assert_eq(_kinds(r).count(&"quest_entry"), 4)
	assert_eq(_kinds(r).count(&"quest_return"), 3)
	for dest in r.requests:
		if dest["kind"] != &"scene":
			assert_false(dest.has("on_miss"), "entries and returns are not gated by rhythm")
	assert_true(seen.size() >= 6)


func _first_onward(r: RouterTest.Rig) -> bool:
	for o in r.router.options():
		if o["kind"] == "scene" and not str(o["object"]).ends_with(".back") and o["to"] != NarrativeGraph.CHECKPOINT:
			return r.go(o["object"])
	return false


func test_route_2_alien_ember_and_back_then_mental_hospital_squadron_and_back() -> void:
	var g := GraphTest.graph()
	var r := RouterTest.rig()
	var seen := {}
	_check_choices(r, seen)
	assert_true(_walk_to(r, "main/mothership"), "to the Alien Spaceship")
	assert_eq(r.router.state.location, "alien_spaceship")
	_check_choices(r, seen)
	assert_true(r.go("mothership.enter_ember"))
	assert_eq(r.requests.back()["kind"], &"quest_entry")
	assert_eq(r.scene(), "ember/hollow")
	assert_eq(r.router.state.checkpoint, "main/mothership")
	_check_choices(r, seen)
	assert_true(_first_onward(r))
	var ford := r.scene()
	assert_true(ford != "ember/hollow")
	_check_choices(r, seen)
	assert_true(r.go("ember.return"))
	assert_eq(r.scene(), "main/mothership", "the return lands on the Alien Spaceship hub")
	assert_eq(r.router.state.progress_of("ember")["scene"], ford)
	# then, in the walkable order, the Mental Hospital
	assert_true(_walk_to(r, "main/ward"), "to the Mental Hospital")
	assert_eq(r.router.state.location, "mental_hospital")
	assert_true(r.router.state.history.find("main/mothership") < r.router.state.history.find("main/ward"))
	_check_choices(r, seen)
	assert_true(r.go("ward.enter_squadron"))
	assert_eq(r.scene(), "squadron/base")
	assert_eq(r.router.state.checkpoint, "main/ward")
	_check_choices(r, seen)
	assert_true(_first_onward(r))
	var cot := r.scene()
	_check_choices(r, seen)
	assert_true(r.go("squadron.return"))
	assert_eq(r.scene(), "main/ward")
	# in again: resumes at the scene left, not at the briefing room
	assert_true(r.go("ward.enter_squadron"))
	assert_eq(r.scene(), cot)
	assert_eq(int(r.router.state.progress_of("squadron")["visits"]), 2)
	assert_true(r.go("squadron.return"))
	# the Ember is unfinished: entering it from the Mental Hospital resumes at the Ford
	assert_true(r.go("ward.enter_ember"))
	assert_eq(r.scene(), ford)
	assert_eq(r.router.state.checkpoint, "main/ward", "the return now lands on the hub entered from this time")
	assert_true(r.go("ember.return"))
	assert_eq(r.scene(), "main/ward")
	assert_eq(r.errors(), [])
	assert_eq(_kinds(r).count(&"quest_return"), 4)
	assert_eq(r.router.state.quest, "")


func test_route_3_hell_dungeon_and_back_then_jesus_and_back_with_a_change_of_mind() -> void:
	var g := GraphTest.graph()
	var r := RouterTest.rig()
	var seen := {}
	assert_true(_walk_to(r, "main/underworld"), "to Hell (a missed last block at the Door)")
	assert_eq(r.router.state.location, "hell")
	_check_choices(r, seen)
	assert_true(r.go("underworld.enter_bassment"))
	assert_eq(r.scene(), "bassment/1")
	assert_eq(r.router.state.checkpoint, "main/underworld")
	_check_choices(r, seen)
	assert_true(r.go("trial.1.0"))
	assert_eq(r.scene(), "bassment/3")
	_check_choices(r, seen)
	assert_true(r.go("bassment.return"))
	assert_eq(r.scene(), "main/underworld")
	assert_eq(r.router.state.progress_of("bassment")["scene"], "bassment/3")
	# a change of mind before the lock: the committed state is byte for byte as it was
	var after_return := r.snap()
	var saves := r.store.saves
	var id := r.tap("underworld.enter_gospel")
	assert_true(id > 0)
	assert_eq(r.snap(), after_return)
	assert_true(r.mock.cancel(id))
	assert_eq(r.closed.back(), [id, &"cancelled"])
	assert_eq(r.snap(), after_return)
	assert_eq(r.store.saves, saves, "nothing was saved for a request that was cancelled")
	assert_true(r.router.state.pending.is_empty())
	# and again, this time to the end
	assert_true(r.go("underworld.enter_gospel"))
	assert_eq(r.scene(), "gospel/jordan")
	assert_eq(r.router.state.checkpoint, "main/underworld")
	_check_choices(r, seen)
	assert_true(r.go("gospel.return"), "the return at once, in the first scene")
	assert_eq(r.scene(), "main/underworld")
	assert_eq(r.router.state.progress_of("gospel")["scene"], "gospel/jordan")
	assert_true(r.go("underworld.enter_gospel"))
	assert_eq(r.scene(), "gospel/jordan")
	assert_eq(int(r.router.state.progress_of("gospel")["visits"]), 2)
	assert_true(r.go("gospel.return"))
	assert_eq(r.errors(), [])
	assert_eq(r.router.state.quest, "")
	for dest in r.requests:
		if dest["kind"] != &"scene":
			assert_false(dest.has("on_miss"))
	# the failure case of the conformance suite: a destination that fails after the lock lands on `landed`, and the saved state describes it
	assert_true(r.go("underworld.enter_bassment"))
	assert_eq(r.scene(), "bassment/3", "resumes at the saved passage")
	r.mock.fail_after_lock_ids.assign(["main/underworld"])
	r.mock.fallback_dest = {"id": "main/underworld", "path": "main", "node": "underworld", "kind": &"scene", "quest": ""}
	assert_true(r.go("bassment.return"))
	assert_true(bool(r.landed_log.back()[1]["fallback"]))
	assert_eq(r.router.state.quest, "")
	assert_eq(r.scene(), "main/underworld")
	assert_eq(r.errors(), [])
