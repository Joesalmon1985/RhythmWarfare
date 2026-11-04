extends TestCase
## The Deathtrap Dungeon opening: the verified links, both entrance choices, routes that rejoin, a fight with retry, the phrase on the pads, the wizard's
## option in the Warehouse and the ordinary Warehouse exit.

## The edges of the book-verified backbone (DuelMasterBattle DD/Deathtrap_Dungeon_Verified_Backbone.json) for the opening passages.
const VERIFIED := {
	1: [["open named box", 270], ["continue north", 66]],
	270: [["continue", 56]],
	66: [["west", 293], ["east", 119]],
	119: [["continue east", 56], ["return and go west", 293]],
}


func _data() -> TrialData:
	var d := TrialData.load_default()
	assert_eq(d.errors, [], "the Trial data validates")
	return d


## Plays a route through the flow alone: every phrase passes. `picks` are choice indexes.
func _walk(picks: Array) -> TrialFlow:
	var f := TrialFlow.new(_data())
	for i in picks:
		var r := f.select(i)
		if r["kind"] == "phrase":
			f.phrase_done(true, 1.0)
	return f


func test_the_links_are_the_verified_ones() -> void:
	var d := _data()
	for n in VERIFIED:
		var got: Array = []
		for c in d.choices(n):
			got.append([str(c["book"]), int(c["to"])])
		assert_eq(got, VERIFIED[n], "passage %d keeps its verified edges" % n)
		assert_eq(d.passage(n)["status"], "BOOK_VERIFIED")
	for n in [56, 293]:
		assert_true(bool(d.passage(n)["endpoint"]), "%d is a prototype endpoint" % n)
		assert_eq(d.passage(n)["status"], "PROTOTYPE_ENDPOINT")
	assert_eq(d.reachable(), [1, 56, 66, 119, 270, 293])
	assert_eq(str(d.encounters["giant_fly"]["placement"]), "ADAPTED", "the adapted placement is labelled")


func test_the_first_entrance_choice_opens_the_named_box() -> void:
	var f := TrialFlow.new(_data())
	assert_eq(f.passage, 1)
	assert_eq((f.choices() as Array).size(), 2)
	var r := f.select(0)
	assert_eq(r["kind"], "phrase", "a choice is followed by a phrase on the pads")
	assert_eq(f.state, TrialFlow.State.PHRASE)
	assert_eq(f.passage, 1, "nothing moves until the phrase is passed")
	var p := f.phrase_done(true, 0.9)
	assert_eq(p["kind"], "pass")
	assert_eq(f.passage, 270)
	assert_true(f.consequence != "", "the consequence is shown with the next choices")
	assert_eq((f.choices() as Array).size(), 1)
	f.select(0)
	f.phrase_done(true, 1.0)
	assert_eq(f.passage, 56)
	assert_true(f.is_endpoint())


func test_the_second_entrance_choice_goes_north_to_the_fork() -> void:
	var f := _walk([1])
	assert_eq(f.passage, 66)
	assert_eq((f.choices() as Array).size(), 2)
	assert_eq(_walk([1, 0]).passage, 293)
	assert_eq(_walk([1, 1]).passage, 119)


func test_routes_rejoin() -> void:
	assert_eq(_walk([0, 0]).passage, 56, "1 > 270 > 56")
	assert_eq(_walk([1, 1, 0]).passage, 56, "1 > 66 > 119 > 56: the east loop reconnects")
	assert_eq(_walk([1, 0]).passage, 293, "1 > 66 > 293")
	assert_eq(_walk([1, 1, 1]).passage, 293, "1 > 66 > 119 > back west > 293")


func test_a_failed_phrase_can_be_retried_and_a_fight_has_an_outcome() -> void:
	var f := _walk([1, 1])
	assert_eq(f.passage, 119)
	var r := f.select(0)
	assert_eq(r["encounter"], "giant_fly")
	var lose := f.phrase_done(false, 0.2)
	assert_eq(lose["kind"], "fail")
	assert_eq(lose["outcome"], "lose", "a lost fight plays the losing animation")
	assert_eq(f.passage, 119, "still in the same passage with the same choices")
	assert_eq(f.retry_index, 0, "the failed choice is marked for a retry")
	assert_true(f.failure != "")
	assert_eq((f.choices() as Array).size(), 2)
	f.select(0)
	var win := f.phrase_done(true, 0.8)
	assert_eq(win["outcome"], "win")
	assert_eq(f.passage, 56)
	assert_eq(f.attempts, 0)
	var kinds: Array = f.history.map(func(h: Dictionary) -> String: return str(h["result"]))
	assert_eq(kinds.count("fail"), 1)


func test_an_endpoint_only_offers_the_way_back() -> void:
	var f := _walk([0, 0])
	assert_eq((f.choices() as Array).size(), 1)
	var r := f.select(0)
	assert_eq(r["kind"], "exit")
	assert_eq(f.exit, "warehouse")
	assert_eq(f.state, TrialFlow.State.ENDED)
	assert_eq(f.select(0)["kind"], "ignored", "nothing else can be done once out")


## Plays the engine by hand: `bot` is "perfect" (every cue), "none" or "no_fights" (every cue but a fight's); `picks` is [[song time, choice index], ...].
func _drive(e: TrialEngine, bot: String, until: float, picks: Array = []) -> Array:
	var log: Array = []
	var t := -e.count_in_s()
	var pressed := {}
	var released := {}
	var done := {}
	while t < until and not e.exited:
		for k in picks.size():
			if t >= float(picks[k][0]) and not done.has(k):
				done[k] = true
				e.select(int(picks[k][1]))
		log.append_array(e.update(t))
		if bot != "none":
			for i in range(maxi(e.level.notes.size() - 300, 0), e.level.notes.size()):
				var n: Dictionary = e.level.notes[i]
				if bot == "no_fights" and str(n.get("enc", "")) != "":
					continue
				if not pressed.has(i) and float(n["time"]) <= t:
					pressed[i] = true
					e.press(int(n["pad"]), float(n["time"]))
				if pressed.has(i) and not released.has(i) and n["type"] == "hold" and float(n["end_time"]) <= t:
					released[i] = true
					e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 60.0
	return log


func _kinds(log: Array, kind: String) -> Array:
	return log.filter(func(x: Dictionary) -> bool: return x["kind"] == kind)


func _engine() -> TrialEngine:
	var e := TrialEngine.new(_data(), RunData.load_default())
	e.begin()
	return e


func test_the_music_game_never_stops() -> void:
	var e := _engine()
	_drive(e, "perfect", 70.0 * e.beat_s)
	var times: Array = []
	for n in e.level.notes:
		times.append(float(n["time"]))
	times.sort()
	var max_gap := 0.0
	for i in range(1, times.size()):
		if times[i] > 0.0 and times[i] < 60.0 * e.beat_s:
			max_gap = maxf(max_gap, (times[i] - times[i - 1]) / e.beat_s)
	assert_true(max_gap <= 6.0, "no more than six beats without a cue, through windows, phrases and results (longest %.2f beats)" % max_gap)
	for b in 4:
		var count := 0
		for n in e.level.notes:
			if int(n["block"]) == b:
				count += 1
		assert_true(count >= 3, "block %d carries cues (%d)" % [b, count])
	# the count-in: cues are already charted for the first downbeat and the first window is open
	assert_true(e.level.notes.size() > 0 and float(e.level.notes[0]["time"]) >= 0.0)


func test_a_choice_window_is_four_bars_and_the_default_is_taken_when_nobody_chooses() -> void:
	var e := _engine()
	var log := _drive(e, "perfect", 120.0 * e.beat_s)
	var opens := _kinds(log, "window_open")
	assert_true(opens.size() >= 3)
	for o in opens:
		assert_near((float(o["closes"]) - float(o["t"])) / e.beat_s, 16.0, 1e-6, "the window is 16 beats: four bars")
	var commits := _kinds(log, "commit")
	assert_true(commits.size() >= 2)
	for c in commits:
		assert_true(bool(c["defaulted"]), "nobody chose")
	var seen: Array = []
	for p in _kinds(log, "passage"):
		seen.append(int(p["passage"]))
	assert_eq(seen.slice(0, 3), [1, 270, 56], "the defaults: open the named box, carry on, then the endpoint")
	assert_true(e.exited)
	assert_eq(e.exit_to, "warehouse", "the endpoint's default is the way out")


func test_the_commit_lands_on_the_decision_beat_of_the_window_that_closes() -> void:
	var e := _engine()
	var log := _drive(e, "perfect", 20.0 * e.beat_s)
	var c: Dictionary = _kinds(log, "commit")[0]
	assert_near(float(c["t"]), e.decision_t(0), 1e-6)
	assert_near(float(c["t"]) / e.beat_s, 12.75, 1e-6)
	assert_near(e.count_in_s() / e.beat_s, 3.25, 1e-6, "the first window opens in the count-in")


func test_a_pick_beats_the_default_and_can_be_changed_until_the_window_closes() -> void:
	var e := _engine()
	var t := e.decision_t(0)
	var log := _drive(e, "perfect", 40.0 * e.beat_s, [[1.0, 0], [2.0, 1], [t + 0.5, 0]])
	var first: Dictionary = _kinds(log, "commit")[0]
	assert_eq(int(first["choice"]), 1, "the last pick before the window closed (the later one came too late)")
	assert_false(bool(first["defaulted"]))
	assert_true(e.select(0) == false or e.window_open, "after the commit the old window no longer takes picks")
	var passages: Array = _kinds(log, "passage").map(func(p: Dictionary) -> int: return int(p["passage"]))
	assert_true(66 in passages, "north: the fork")


func test_a_pass_shows_the_consequence_and_the_next_choices() -> void:
	var e := _engine()
	var log := _drive(e, "perfect", 40.0 * e.beat_s)
	var res: Dictionary = _kinds(log, "result")[0]
	assert_eq(res["result"], "pass")
	var after := _kinds(log, "passage").filter(func(p: Dictionary) -> bool: return int(p["passage"]) == 270)
	assert_eq(after.size(), 1)
	assert_true(str(after[0]["consequence"]) != "")
	var ev := _kinds(log, "window_open").filter(func(w: Dictionary) -> bool: return int(w["passage"]) == 270)
	assert_eq(ev.size(), 1, "and its choices are open at once")
	assert_near(float(ev[0]["t"]), float(res["t"]), 1e-6)


func test_a_failed_phrase_reopens_the_window_with_the_failed_option_as_the_default() -> void:
	var e := _engine()
	var log := _drive(e, "none", 36.0 * e.beat_s)
	var res := _kinds(log, "result")
	assert_true(res.size() >= 1)
	assert_eq(res[0]["result"], "fail")
	assert_eq(e.flow.passage, 1, "still in the first passage")
	assert_eq(e.flow.retry_index, 0)
	assert_eq(e.default_index(), 0, "doing nothing tries the same option again")
	assert_true(e.window_open)


func test_the_fight_loses_then_the_retry_wins() -> void:
	var e := _engine()
	var block := 16.0 * e.beat_s
	# north (pick 1), east (pick 1), then the fly (pick 0) played badly; then retried by default and played well
	var picks := [[1.0, 1], [2.0 * block + 1.0, 1], [4.0 * block + 1.0, 0]]
	var log := _drive(e, "no_fights", 9.0 * block, picks)
	var results: Array = _kinds(log, "result")
	var seq: Array = results.map(func(r: Dictionary) -> String: return str(r["result"]))
	assert_true(seq.size() >= 3, str(seq))
	var fights := results.filter(func(r: Dictionary) -> bool: return bool(r["fight"]))
	assert_true(fights.size() >= 1)
	assert_eq(fights[0]["outcome"], "lose")
	assert_eq(e.flow.passage, 119, "the lost fight stays at the curtain")
	var e2 := _engine()
	var log2 := _drive(e2, "perfect", 10.0 * block, picks)
	var passages: Array = _kinds(log2, "passage").map(func(p: Dictionary) -> int: return int(p["passage"]))
	assert_true(56 in passages, "a perfect player passes the fight: %s" % str(passages))
	assert_true(_kinds(log2, "result").any(func(r: Dictionary) -> bool: return bool(r["fight"]) and r["outcome"] == "win"))


func _trial_scene(bot: String) -> Dictionary:
	OS.set_environment("RW_TRIAL_VIRTUAL", "1")
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/trial/trial_play.tscn") as PackedScene).instantiate()
	scene.bot = bot
	host.add_child(scene)
	scene.size = Vector2(844, 390)
	var exits: Array = []
	scene.exit_launcher = func(where: String) -> void: exits.append(where)
	return {"host": host, "scene": scene, "exits": exits}


## Steps the scene's virtual clock until `cond` holds (or `limit_s` of song time has passed). Returns whether it held.
func _until(scene: Node, cond: Callable, limit_s: float = 90.0) -> bool:
	var t := 0.0
	while t < limit_s:
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
		t += 1.0 / 30.0
		if cond.call():
			return true
	return false


func _free_scene(d: Dictionary) -> void:
	(d["host"] as Control).queue_free()
	OS.set_environment("RW_TRIAL_VIRTUAL", "")


func test_the_scene_floats_choices_over_pads_that_keep_playing() -> void:
	var d := _trial_scene("perfect")
	var scene: Node = d["scene"]
	assert_eq(scene._buttons.size(), 2, "two floating choices")
	for b in scene._buttons:
		assert_true((b as Button).size.x >= 140.0 and (b as Button).size.y >= 40.0, "a big enough target on a phone")
	assert_true(scene._buttons[0].text.contains("[DEFAULT]"), "one is marked as the default")
	assert_false(scene._buttons[1].text.contains("[DEFAULT]"))
	assert_true(scene._pic.texture != null, "a fixed illustrated scene")
	assert_true(scene._desc.text.length() > 40, "with a short description")
	assert_true(scene._choice_layer.visible)
	scene.pick(1)
	assert_true(scene._buttons[1].text.contains("[CHOSEN]") and not scene._buttons[0].text.contains("[DEFAULT]"), "a pick replaces the default mark")
	scene.pick(0)
	assert_true(scene._buttons[0].text.contains("[CHOSEN]"), "and can be changed")
	scene.pick(1)
	var cues_before: int = scene.engine.level.notes.size()
	assert_true(_until(scene, func() -> bool: return scene.engine.flow.passage == 66))
	assert_true(scene.engine.level.notes.size() > cues_before, "cues were being charted all along")
	# during the phrase block the choices are away and the scene is clear; the pads still have cues
	var saw_phrase_hidden := false
	var t := 0.0
	var free := 0
	while t < 40.0 and scene.engine.flow.passage == 66:
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
		t += 1.0 / 30.0
		if scene.engine.kind == "phrase" and not scene.engine.window_open:
			saw_phrase_hidden = saw_phrase_hidden or not scene._choice_layer.visible
		if scene.engine.window_open and scene._timer_label.text.begins_with("4 bar"):
			free += 1
		if free > 3:
			scene.pick(1)
			break
	assert_true(free > 0, "the window shows how many bars are left")
	_free_scene(d)


func test_nothing_chosen_means_the_default_and_the_endpoint_leaves() -> void:
	var d := _trial_scene("perfect")
	var scene: Node = d["scene"]
	assert_true(_until(scene, func() -> bool: return not (d["exits"] as Array).is_empty(), 120.0), "doing nothing walks the default route out")
	assert_eq(d["exits"], ["warehouse"])
	var passages: Array = []
	for e in scene.trace:
		if e["kind"] == "passage":
			passages.append(int(e["passage"]))
	assert_eq(passages.slice(0, 3), [1, 270, 56], "1 > 270 > 56 by defaults alone")
	var defaulted: Array = scene.trace.filter(func(e: Dictionary) -> bool: return e["kind"] == "commit" and bool(e["defaulted"]))
	assert_true(defaulted.size() >= 3)
	_free_scene(d)


func test_the_fight_fails_then_is_retried_and_won_in_the_scene() -> void:
	var d := _trial_scene("perfect")
	var scene: Node = d["scene"]
	var win_window := func(p: int) -> bool: return scene.engine.window_open and scene.engine.flow.passage == p and scene._buttons.size() > 0
	assert_true(_until(scene, func() -> bool: return win_window.call(1)))
	scene.pick(1)  # north
	assert_true(_until(scene, func() -> bool: return win_window.call(66)))
	scene.pick(1)  # east
	assert_true(_until(scene, func() -> bool: return win_window.call(119)))
	scene.bot = "no_fights"  # the player sits this one out
	scene.pick(0)  # push through the curtain: the Giant Fly
	assert_true(_until(scene, func() -> bool: return scene._enemy.visible), "the fly is on screen for the fight")
	assert_true(_until(scene, func() -> bool: return not scene._outcome.is_empty()), "an outcome animation plays")
	assert_true(_until(scene, func() -> bool: return win_window.call(119) and scene._outcome.is_empty()))
	assert_true(scene._buttons[0].text.begins_with("Try again"), "the retry is offered: " + scene._buttons[0].text)
	assert_true(scene._news.text.contains("stings"), scene._news.text)
	assert_true(scene._buttons[0].text.contains("[DEFAULT]"), "and doing nothing retries it")
	scene.bot = "perfect"
	assert_true(_until(scene, func() -> bool: return scene.engine.flow.passage == 56), "the retry is passed")
	var results: Array = []
	for e in scene.trace:
		if e["kind"] == "result":
			results.append(str(e["result"]))
	assert_eq(results, ["pass", "pass", "fail", "pass"], "the two walks, the lost fight, the won retry")
	_free_scene(d)


func _run_scene(start: String) -> Dictionary:
	OS.set_environment("RW_RUN_VIRTUAL", "1")
	OS.set_environment("RW_RUN_BOT", "perfect")
	OS.set_environment("RW_RUN_ROUTES", "")
	Session.run_start_node = start
	var host := Control.new()
	host.size = Vector2(844, 390)
	tree.root.add_child(host)
	var scene: Control = (load("res://src/run/run_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	scene.size = Vector2(844, 390)
	return {"host": host, "scene": scene}


func test_the_wizard_offers_the_trial_in_the_warehouse_only() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	assert_true(scene._gate.visible, "the wizard is in the Warehouse")
	assert_eq(scene._gate_btn.text, "Enter the Trial")
	var launched: Array = []
	scene.trial_launcher = func() -> void: launched.append("trial")
	scene._gate_btn.pressed.emit()
	assert_eq(launched, ["trial"], "choosing the option leaves for the dungeon")
	var gate_rect := Rect2(scene._gate_btn.position, scene._gate_btn.size).merge(Rect2(scene._gate_wizard.position, scene._gate_wizard.size))
	var rects: Dictionary = scene.pad_view.button_rects()
	for p in rects:
		assert_false(gate_rect.intersects(rects[p] as Rect2), "the option does not sit on pad %d" % p)
	(d["host"] as Control).queue_free()
	var m := _run_scene("mothership")
	assert_false((m["scene"] as Node)._gate.visible, "no wizard outside the Warehouse")
	(m["host"] as Control).queue_free()
	Session.run_progress = saved
	DirAccess.remove_absolute("user://test_trial_save.json")
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")


func test_ignoring_the_wizard_leaves_the_warehouse_the_ordinary_way() -> void:
	var saved := Session.run_progress
	Session.run_progress = RunProgress.load_data("user://test_trial_save2.json", "user://none.json")
	var d := _run_scene("")
	var scene: Node = d["scene"]
	var launched: Array = []
	scene.trial_launcher = func() -> void: launched.append("trial")
	var beat := 60.0 / 174.0
	var t: float = scene._vt
	while t < 64.0 * beat + 0.3:
		t += 1.0 / 30.0
		scene._vt = t
		scene._step_virtual(t)
	assert_eq(launched, [], "nothing took the player into the dungeon")
	assert_eq(scene.engine.node_id, "mothership", "the run went on by its default route")
	assert_false(scene._gate.visible, "and the wizard stayed behind in the Warehouse")
	(d["host"] as Control).queue_free()
	Session.run_progress = saved
	DirAccess.remove_absolute("user://test_trial_save2.json")
	OS.set_environment("RW_RUN_VIRTUAL", "")
	OS.set_environment("RW_RUN_BOT", "")


func test_the_whole_quest_is_mapped() -> void:
	var m: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://content/trial/quest_map.json"))
	assert_eq(int(m["start"]), 1)
	assert_eq(int(m["victory"]), 400)
	var zones: Array = m["zones"]
	assert_eq(zones.size(), 17, "the 17 physical zones of the adaptation")
	var ids := {}
	for z in zones:
		ids[str(z["id"])] = true
	var route: Array = m["route"]
	assert_eq(route[0], "dd_entrance")
	assert_eq(route[route.size() - 2], "dd_igbut")
	assert_eq(route[route.size() - 1], "dd_exit", "from the first corridor to daylight")
	for z in zones:
		for e in z["exits"]:
			assert_true(ids.has(str(e["to"])) or str(e["to"]) == "dd_exit", "%s exits to a known zone (%s)" % [z["id"], e["to"]])
	var passages: Dictionary = m["passages"]
	var verified := 0
	for k in passages:
		var p: Dictionary = passages[k]
		if str(p["status"]) == "BOOK_VERIFIED" or str(p["status"]) == "PROTOTYPE_ENDPOINT":
			verified += 1
		assert_true(ids.has(str(p["zone"])), "passage %s sits in a zone" % k)
		for e in p["edges"]:
			var tos: Array = e["to"] if typeof(e["to"]) == TYPE_ARRAY else [e["to"]]
			for to in tos:
				assert_true(passages.has(str(int(to))), "passage %s links to %d, which the map holds" % [k, int(to)])
	assert_true(verified >= 28, "every book-verified passage is in the map (%d)" % verified)
	assert_true(passages.size() >= 60, "and the passages they point at (%d)" % passages.size())
	assert_eq(str(passages["400"]["zone"]), "dd_igbut", "victory sits behind Igbut's door")
	for g in ["emerald", "sapphire", "diamond", "final_use"]:
		assert_true(ids.has(str(m["gems"][g]["zone"])), g)
	var d := _data()
	for n in d.passages:
		assert_true(passages.has(str(n)), "the playable passage %d is on the map" % n)
	assert_true((m["encounters"] as Array).size() >= 12, "the major encounters are listed")
