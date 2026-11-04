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


func test_the_phrase_is_charted_on_the_clock_and_judged() -> void:
	var rd := RunData.load_default()
	var td := _data()
	var pack: Dictionary = rd.packs[td.raw["music"]["chart"]]
	var lv := Level.new()
	lv.mode = "defense"
	var j := PadJudge.new()
	j.setup(lv.notes, [])
	var ph := TrialPhrase.new()
	ph.setup(lv, j, 174.0, 0.6)
	var spec: Dictionary = td.phrases["easy"]
	var n := ph.start(pack, spec, 10.0)
	assert_true(n >= 3, "a short phrase has a few cues (%d)" % n)
	var beat := 60.0 / 174.0
	for i in range(ph.first, ph.first + ph.count):
		var cue: Dictionary = lv.notes[i]
		var rel := (float(cue["time"]) - 10.0) / beat
		assert_near(rel * 2.0, roundf(rel * 2.0), 1e-6, "cues sit on the music's half beats")
		assert_true(float(cue["time"]) < ph.end_t)
	for i in range(ph.first, ph.first + ph.count):  # a perfect player passes
		var cue2: Dictionary = lv.notes[i]
		j.press(int(cue2["pad"]), float(cue2["time"]))
		if cue2["type"] == "hold":
			j.release(int(cue2["pad"]), float(cue2["end_time"]))
	var res := ph.update(ph.end_t + 0.5)
	assert_true(bool(res["passed"]))
	var n2 := ph.start(pack, spec, 30.0)  # an absent player fails; the second attempt on the same list is independent
	assert_eq(n2, n)
	var res2 := ph.update(ph.end_t + 0.5)
	assert_false(bool(res2["passed"]))
	assert_near(float(res2["credit"]), 0.0, 1e-9)
	var fight := ph.start(pack, td.phrases["fight"], 50.0)
	assert_true(fight > n, "the fight phrase has more cues (%d against %d)" % [fight, n])


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


func _until_scene(scene: Node, limit_s: float = 60.0) -> void:
	var t := 0.0
	while t < limit_s:
		scene._vt += 1.0 / 30.0
		scene._step_virtual(scene._vt)
		t += 1.0 / 30.0
		if scene.mode == "scene" or scene.mode == "ended":
			return


func test_the_scene_plays_a_phrase_with_floating_choices_and_the_pads() -> void:
	var d := _trial_scene("perfect")
	var scene: Node = d["scene"]
	assert_eq(scene.mode, "scene")
	assert_eq(scene._buttons.size(), 2, "two floating choices")
	for b in scene._buttons:
		assert_true((b as Button).size.x >= 140.0 and (b as Button).size.y >= 40.0, "a big enough target on a phone")
	assert_true(scene._pic.texture != null, "a fixed illustrated scene")
	assert_true(scene._desc.text.length() > 40, "with a short description")
	scene.pick(0)
	assert_eq(scene.mode, "lead")
	assert_false(scene._choice_layer.visible, "the choices step aside for the pads")
	_until_scene(scene)
	assert_eq(scene.flow.passage, 270, "a passed phrase shows the consequence and the next choices")
	assert_true(scene._news.visible and scene._news.text != "")
	assert_eq(scene._buttons.size(), 1)
	scene.pick(0)
	_until_scene(scene)
	assert_eq(scene.flow.passage, 56)
	assert_eq(scene._buttons[0].text, "Return to the Warehouse")
	scene.pick(0)
	assert_eq(d["exits"], ["warehouse"])
	(d["host"] as Control).queue_free()
	OS.set_environment("RW_TRIAL_VIRTUAL", "")


func test_the_fight_fails_then_is_retried_and_won() -> void:
	var d := _trial_scene("perfect")
	var scene: Node = d["scene"]
	scene.pick(1)  # north
	_until_scene(scene)
	assert_eq(scene.flow.passage, 66)
	scene.pick(1)  # east
	_until_scene(scene)
	assert_eq(scene.flow.passage, 119)
	scene.bot = "none"  # the player sits this one out
	scene.pick(0)  # push through the curtain: the Giant Fly
	assert_true(scene._enemy.visible, "the fly is on screen for the fight")
	_until_scene(scene)  # the player plays nothing
	assert_eq(scene.flow.passage, 119, "a failed fight stays put")
	assert_true(scene._buttons[0].text.begins_with("Try again"), "and offers the retry: " + scene._buttons[0].text)
	assert_true(scene._news.text.contains("stings"), scene._news.text)
	scene.bot = "perfect"
	scene.pick(0)
	_until_scene(scene)
	assert_eq(scene.flow.passage, 56, "retried and passed")
	var results: Array = []
	for t in scene.trace:
		if t["kind"] == "result":
			results.append(str(t["result"]))
	assert_eq(results, ["pass", "pass", "fail", "pass"], "results in order: the two walks, the lost fight, the won retry")
	(d["host"] as Control).queue_free()
	OS.set_environment("RW_TRIAL_VIRTUAL", "")


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
