extends TestCase
## The wizard duel: the numbers (DuelRules), the score book (DuelMatch), one wizard's phrases (DuelEngine), the scripted players
## (DuelBot), the network messages (DuelNetwork) and the scene wired to them (DuelPlay, solo and virtual time).

var _rules: DuelRules
var _rdata: RunData


func _setup() -> void:
	if _rules == null:
		_rules = DuelRules.load_default()
		_rdata = RunData.load_default()


func _res(cast: bool, power10: int = 0, credit: float = 1.0, family: String = "drums", streak: int = 0) -> Dictionary:
	return {"cast": cast, "power10": power10, "credit": credit, "family": family, "streak": streak}


func _play(skill_a: String, skill_b: String, seed_value: int) -> Dictionary:
	var ea := DuelEngine.new(_rules, _rdata)
	var eb := DuelEngine.new(_rules, _rdata)
	ea.begin()
	eb.begin()
	var ba := DuelBot.from_skill(_rules, skill_a, seed_value)
	var bb := DuelBot.from_skill(_rules, skill_b, seed_value + 1)
	var duel := DuelMatch.new(_rules)
	var t := -ea.count_in_s()
	while not duel.finished and t < 300.0:
		t += 1.0 / 60.0
		ba.step(ea, t)
		bb.step(eb, t)
		for ev in ea.update(t):
			if str(ev["kind"]) == "result":
				duel.submit(0, int(ev["j"]), ev)
		for ev in eb.update(t):
			if str(ev["kind"]) == "result":
				duel.submit(1, int(ev["j"]), ev)
	return {"match": duel, "a": ea, "b": eb}


# --- data -----------------------------------------------------------------------------------------------------------------------

func test_data_loads_and_names_real_packs() -> void:
	_setup()
	assert_eq(_rules.errors.size(), 0, str(_rules.errors))
	assert_eq(_rdata.errors.size(), 0)
	assert_true(_rdata.packs.has(str(_rules.cfg["music"]["audio"])), "audio pack exists")
	assert_true(_rdata.packs.has(str(_rules.cfg["music"]["chart"])), "chart pack exists")
	assert_eq(_rules.phrase_beats(), 8, "a phrase is two bars")
	assert_true(float(_rules.cfg["timing"]["decision_beat"]) < 8.0)


func test_bad_data_is_reported() -> void:
	var r := DuelRules.load_file("res://content/duel/does_not_exist.json")
	assert_true(r.errors.size() > 0)


func test_pattern_and_tiers() -> void:
	_setup()
	assert_eq(_rules.family_of(0), "drums")
	assert_eq(_rules.family_of(2), "bass")
	assert_eq(_rules.family_of(8), "drums", "the pattern repeats")
	assert_eq(_rules.tier_of(0), 1)
	assert_eq(_rules.tier_of(5), 1)
	assert_eq(_rules.tier_of(6), 2)
	assert_eq(_rules.tier_of(100), 4)


func test_power_rises_with_precision_streak_and_tier() -> void:
	_setup()
	var low := _rules.power10(0.4, "drums", 1, 0)
	var mid := _rules.power10(0.7, "drums", 1, 0)
	var high := _rules.power10(1.0, "drums", 1, 0)
	assert_true(low < mid and mid < high, "precision: %d %d %d" % [low, mid, high])
	assert_true(_rules.power10(1.0, "drums", 1, 3) > high, "a streak adds power")
	assert_eq(_rules.power10(1.0, "drums", 1, 5), _rules.power10(1.0, "drums", 1, 50), "the streak bonus is capped")
	assert_true(_rules.power10(1.0, "bass", 1, 0) > high, "bass spells hit harder")
	assert_true(_rules.power10(1.0, "drums", 4, 0) > high, "later tiers hit harder")
	assert_eq(_rules.power10(0.0, "drums", 1, 0), int(round(float(_rules.cfg["power"]["min"]) * 10.0)), "a minimum passing phrase still casts the minimum")


func test_precision_weights_and_strays() -> void:
	_setup()
	assert_near(_rules.precision(4.0, 4, 0), 1.0, 1e-6)
	assert_near(_rules.precision(2.0, 4, 0), 0.5, 1e-6)
	assert_true(_rules.precision(4.0, 4, 3) < 1.0, "strays cost precision")
	assert_eq(_rules.precision(0.0, 4, 100), 0.0, "never below zero")
	assert_true(_rules.grade_weight(10.0, 45.0, 90.0) > _rules.grade_weight(60.0, 45.0, 90.0))
	assert_true(_rules.grade_weight(60.0, 45.0, 90.0) > _rules.grade_weight(120.0, 45.0, 90.0))


# --- the score book -------------------------------------------------------------------------------------------------------------

func test_a_phrase_lands_when_both_results_are_in() -> void:
	_setup()
	var m := DuelMatch.new(_rules)
	assert_eq(m.submit(0, 0, _res(true, 100)).size(), 0, "one result alone does nothing")
	var evs := m.submit(1, 0, _res(true, 60))
	assert_eq(evs.size(), 1)
	assert_eq(evs[0]["kind"], "phrase")
	assert_eq(m.hp10[1], _rules.max_hp10() - 100, "my spell hit the rival")
	assert_eq(m.hp10[0], _rules.max_hp10() - 60, "the rival's spell hit me")
	assert_eq((evs[0]["spells"] as Array).size(), 2)


func test_a_failed_phrase_casts_nothing() -> void:
	_setup()
	var m := DuelMatch.new(_rules)
	m.submit(0, 0, _res(false))
	var evs := m.submit(1, 0, _res(true, 80))
	assert_eq(m.hp10[1], _rules.max_hp10(), "no spell, no damage")
	assert_eq(m.hp10[0], _rules.max_hp10() - 80)
	assert_eq((evs[0]["spells"] as Array).size(), 1)


func test_phrases_resolve_in_order_and_repeats_are_ignored() -> void:
	_setup()
	var m := DuelMatch.new(_rules)
	m.submit(0, 1, _res(true, 50))
	m.submit(1, 1, _res(true, 50))
	assert_eq(m.phrase, 0, "phrase 1 waits for phrase 0")
	assert_eq(m.hp10[0], _rules.max_hp10())
	m.submit(0, 0, _res(true, 10))
	var evs := m.submit(1, 0, _res(true, 10))
	assert_eq(evs.size(), 2, "both resolve, in order")
	assert_eq(int(evs[0]["j"]), 0)
	assert_eq(int(evs[1]["j"]), 1)
	assert_eq(m.submit(0, 1, _res(true, 9999)).size(), 0, "a phrase already resolved is ignored")
	assert_eq(m.hp10[1], _rules.max_hp10() - 60)


func test_knock_out_ends_the_duel() -> void:
	_setup()
	var m := DuelMatch.new(_rules)
	var big := _rules.max_hp10()
	m.submit(0, 0, _res(true, big + 5))
	var evs := m.submit(1, 0, _res(false))
	assert_true(m.finished)
	assert_eq(m.winner, 0)
	assert_eq(m.reason, "ko")
	assert_eq(m.hp10[1], 0, "health stops at zero")
	assert_eq(str(evs[evs.size() - 1]["kind"]), "end")


func test_double_knock_out_goes_to_the_bigger_overkill_or_a_draw() -> void:
	_setup()
	var big := _rules.max_hp10()
	var m := DuelMatch.new(_rules)
	m.submit(0, 0, _res(true, big + 50))
	m.submit(1, 0, _res(true, big + 10))
	assert_eq(m.winner, 0, "the harder hit wins a double knock-out")
	var d := DuelMatch.new(_rules)
	d.submit(0, 0, _res(true, big))
	d.submit(1, 0, _res(true, big))
	assert_eq(d.winner, -1)
	assert_eq(d.reason, "draw")


func test_time_limit_goes_to_the_higher_health() -> void:
	_setup()
	var m := DuelMatch.new(_rules)
	var limit := int(_rules.cfg["max_phrases"])
	for j in limit:
		m.submit(0, j, _res(true, 4 if j == 0 else 0, 1.0))
		m.submit(1, j, _res(false))
	assert_true(m.finished)
	assert_eq(m.winner, 0)
	assert_eq(m.reason, "time")


func test_equal_health_at_the_limit_is_sudden_death() -> void:
	_setup()
	var m := DuelMatch.new(_rules)
	var limit := int(_rules.cfg["max_phrases"])
	for j in limit:
		m.submit(0, j, _res(false))
		m.submit(1, j, _res(false))
	assert_false(m.finished, "equal health: play on")
	assert_true(m.sudden_death)
	m.submit(0, limit, _res(false))
	m.submit(1, limit, _res(true, 30))
	assert_true(m.finished)
	assert_eq(m.winner, 1)
	assert_eq(m.reason, "sudden")


func test_sudden_death_that_never_breaks_is_decided_by_credit_then_draw() -> void:
	_setup()
	var m := DuelMatch.new(_rules)
	var end := int(_rules.cfg["max_phrases"]) + int(_rules.cfg["sudden_death_extra"])
	for j in end:
		m.submit(0, j, _res(false, 0, 0.9))
		m.submit(1, j, _res(false, 0, 0.5))
	assert_true(m.finished)
	assert_eq(m.winner, 0, "more credit over the whole duel")
	var d := DuelMatch.new(_rules)
	for j in end:
		d.submit(0, j, _res(false, 0, 0.5))
		d.submit(1, j, _res(false, 0, 0.5))
	assert_eq(d.winner, -1)


func test_forfeit() -> void:
	_setup()
	var m := DuelMatch.new(_rules)
	m.submit(0, 0, _res(true, 10))
	var evs := m.forfeit(1)
	assert_true(m.finished)
	assert_eq(m.winner, 0)
	assert_eq(m.reason, "forfeit")
	assert_eq(evs.size(), 1)
	assert_eq(m.forfeit(0).size(), 0, "already over")


func test_both_phones_reach_the_same_result() -> void:
	_setup()
	# the same stream of results fed from each wizard's own point of view (sides swapped) agrees
	var rng := RandomNumberGenerator.new()
	rng.seed = 99
	for run in 20:
		var m0 := DuelMatch.new(_rules)
		var m1 := DuelMatch.new(_rules)
		for j in 60:
			var a := _res(rng.randf() < 0.8, rng.randi_range(50, 200))
			var b := _res(rng.randf() < 0.8, rng.randi_range(50, 200))
			m0.submit(0, j, a)
			m0.submit(1, j, b)
			m1.submit(1, j, a)  # the other phone: the roles swapped, and the messages arrive in the other order
			m1.submit(0, j, b)
		assert_eq(m0.finished, m1.finished)
		assert_eq(m0.hp10[0], m1.hp10[1], "my health here is the rival's there")
		assert_eq(m0.hp10[1], m1.hp10[0])
		assert_true(m0.winner == -1 and m1.winner == -1 or m0.winner == 1 - m1.winner, "winner %d vs %d" % [m0.winner, m1.winner])


# --- one wizard's phrases ---------------------------------------------------------------------------------------------------------

func test_cues_fall_in_the_right_places() -> void:
	_setup()
	var e := DuelEngine.new(_rules, _rdata)
	e.begin()
	e.update(0.0)
	var decision := float(_rules.cfg["timing"]["decision_beat"])
	assert_true(e.level.notes.size() > 0)
	for n in e.level.notes:
		var j := int(n["block"])
		var local_beat := float(n["time"]) / e.beat_s - float(j * 8)
		assert_true(local_beat >= 0.0 and local_beat < decision, "cue inside its phrase (beat %f)" % local_beat)
		if str(n["type"]) == "hold":
			assert_true(float(n["end_time"]) / e.beat_s - float(j * 8) <= decision - 0.2, "a hold ends before the judgement")
		if _rules.family_of(j) == "drums":
			assert_true(int(n["pad"]) == 1 or int(n["pad"]) == 4, "drums are on pads 1 and 4")
			assert_eq(str(n["type"]), "tap")
		else:
			assert_eq(str(n["type"]), "hold", "bass phrases are held notes")
	for i in range(1, e.level.notes.size()):
		assert_true(float(e.level.notes[i]["time"]) >= float(e.level.notes[i - 1]["time"]), "cues are in time order")


func test_every_phrase_has_cues_so_it_can_be_judged() -> void:
	_setup()
	var e := DuelEngine.new(_rules, _rdata)
	e.begin()
	e.update(e.phrase_s() * 40.0)
	for j in 40:
		var count := 0
		for n in e.level.notes:
			if int(n["block"]) == j:
				count += 1
		assert_true(count >= 1, "phrase %d has %d cues" % [j, count])


func test_a_perfect_player_casts_every_phrase_with_a_growing_streak() -> void:
	_setup()
	var e := DuelEngine.new(_rules, _rdata)
	e.begin()
	var bot := DuelBot.from_skill(_rules, "archmage", 3)
	bot.hit = 1.0
	bot.sigma_ms = 0.0
	bot.strays = 0.0
	var results: Array = []
	var t := -e.count_in_s()
	while results.size() < 10:
		t += 1.0 / 60.0
		bot.step(e, t)
		for ev in e.update(t):
			if str(ev["kind"]) == "result":
				results.append(ev)
	for i in results.size():
		assert_true(bool(results[i]["cast"]), "phrase %d cast" % i)
		assert_eq(int(results[i]["streak"]), i + 1, "the streak grows")
		assert_near(float(results[i]["credit"]), 1.0, 1e-6)
		assert_eq(int(results[i]["perfect"]), int(results[i]["cues"]), "every cue perfect")
		assert_eq(int(results[i]["j"]), i)
	assert_true(int(results[5]["power10"]) > int(results[0]["power10"]), "power rises with the streak and tier")


func test_a_player_who_plays_nothing_never_casts() -> void:
	_setup()
	var e := DuelEngine.new(_rules, _rdata)
	e.begin()
	var results: Array = []
	var t := -e.count_in_s()
	while results.size() < 6:
		t += 1.0 / 30.0
		for ev in e.update(t):
			if str(ev["kind"]) == "result":
				results.append(ev)
	for r in results:
		assert_false(bool(r["cast"]))
		assert_eq(int(r["power10"]), 0)
		assert_eq(int(r["streak"]), 0)


func test_a_missed_phrase_breaks_the_streak() -> void:
	_setup()
	var e := DuelEngine.new(_rules, _rdata)
	e.begin()
	var bot := DuelBot.from_skill(_rules, "archmage", 4)
	bot.hit = 1.0
	bot.sigma_ms = 0.0
	bot.strays = 0.0
	bot.skip_blocks = {2: true}  # sit out phrase 2
	var t := -e.count_in_s()
	var seen: Array = []
	while seen.size() < 5:
		t += 1.0 / 60.0
		bot.step(e, t)
		for ev in e.update(t):
			if str(ev["kind"]) == "result":
				seen.append(ev)
	assert_true(bool(seen[1]["cast"]))
	assert_false(bool(seen[2]["cast"]), "the silent phrase fizzles")
	assert_eq(int(seen[2]["streak"]), 0)
	assert_true(bool(seen[3]["cast"]))
	assert_eq(int(seen[3]["streak"]), 1, "starting over")


func test_stray_presses_cost_precision_not_the_cast() -> void:
	_setup()
	var e := DuelEngine.new(_rules, _rdata)
	e.begin()
	var t := -e.count_in_s()
	var res: Dictionary = {}
	var stray_done := false
	var bot := DuelBot.from_skill(_rules, "archmage", 5)
	bot.hit = 1.0
	bot.sigma_ms = 0.0
	bot.strays = 0.0
	while res.is_empty():
		t += 1.0 / 60.0
		bot.step(e, t)
		if t > 0.2 and not stray_done:
			stray_done = true
			e.press(2, t, 2)  # no cue on pad 2 in a drums phrase
			e.release(2, t + 0.02, 2)
		for ev in e.update(t):
			if str(ev["kind"]) == "result":
				res = ev
	assert_true(bool(res["cast"]))
	assert_eq(int(res["strays"]), 1)
	assert_true(float(res["precision"]) < 1.0)


func test_results_survive_the_wire_exactly() -> void:
	_setup()
	var e := DuelEngine.new(_rules, _rdata)
	e.begin()
	var bot := DuelBot.from_skill(_rules, "adept", 8)
	var t := -e.count_in_s()
	while e.results.size() < 6:
		t += 1.0 / 60.0
		bot.step(e, t)
		e.update(t)
	for r in e.results:
		var msg: Dictionary = (r as Dictionary).duplicate()
		msg["t"] = "res"
		msg.erase("kind")
		var back: Variant = JSON.parse_string(JSON.stringify(msg))
		assert_eq(int(back["power10"]), int(r["power10"]))
		assert_eq(int(back["j"]), int(r["j"]))
		assert_eq(bool(back["cast"]), bool(r["cast"]))
		assert_near(float(back["credit"]), float(r["credit"]), 1e-9)


# --- whole duels between scripted players -----------------------------------------------------------------------------------------------

func test_the_better_player_wins_and_a_duel_takes_a_real_length() -> void:
	_setup()
	var wins := 0
	var lengths := 0
	for s in 5:
		var d := _play("archmage", "apprentice", 100 + s * 13)
		var m: DuelMatch = d["match"]
		assert_true(m.finished, "the duel ends")
		if m.winner == 0:
			wins += 1
		lengths += m.phrase
	assert_true(wins >= 4, "the archmage beats the apprentice (%d of 5)" % wins)
	var mean_s := float(lengths) / 5.0 * 8.0 * 60.0 / 174.0
	assert_true(mean_s >= 30.0 and mean_s <= 100.0, "a duel lasts %.0f s" % mean_s)


func test_even_players_both_win_sometimes() -> void:
	_setup()
	var wins := [0, 0]
	for s in 8:
		var m: DuelMatch = _play("adept", "adept", 500 + s * 31)["match"]
		if m.winner >= 0:
			wins[m.winner] += 1
	assert_true(wins[0] >= 1 and wins[1] >= 1, "%s" % str(wins))


# --- the network messages ------------------------------------------------------------------------------------------------------------

func _net() -> Node:
	return tree.root.get_node("DuelNetwork")


func _packet(msg: Dictionary) -> PackedByteArray:
	return JSON.stringify(msg).to_utf8_buffer()


func test_the_link_handles_hello_ping_and_messages() -> void:
	var net := _net()
	net.close("")
	assert_eq(net.state, net.State.IDLE)
	net._on_packet(1, _packet({"t": "hello", "name": "Merlin", "v": net.PROTOCOL}))
	assert_eq(net.opp_name, "Merlin")
	assert_eq(net.state, net.State.CONNECTED)
	net._on_packet(1, _packet({"t": "res", "j": 3, "cast": true, "power10": 77, "r": 1}))
	net._on_packet(1, _packet({"t": "pong", "s": Time.get_ticks_usec() - 20000}))
	assert_true(net.rtt_ms > 5.0 and net.rtt_ms < 500.0, "rtt %f" % net.rtt_ms)
	net._on_packet(1, _packet({"t": "ping", "s": 1}))  # answered here, never shown to a scene
	var inbox: Array = net.drain()
	assert_eq(inbox.size(), 1)
	assert_eq(inbox[0]["t"], "res")
	assert_eq(int(inbox[0]["power10"]), 77)
	assert_eq(net.drain().size(), 0, "drained")
	net._on_packet(1, PackedByteArray([1, 2, 3]))  # garbage is ignored
	net._on_packet(1, _packet({"t": "bye"}))
	var after: Array = net.drain()
	assert_eq(after.size(), 1)
	assert_eq(after[0]["t"], "closed")
	assert_eq(after[0]["why"], "left")
	assert_true(after[0]["had_game"])
	net.close("")


func test_the_link_refuses_another_version() -> void:
	var net := _net()
	net.close("")
	net.state = net.State.JOINING
	net._on_packet(1, _packet({"t": "hello", "name": "Old", "v": 0}))
	var inbox: Array = net.drain()
	assert_eq(inbox.size(), 1)
	assert_eq(inbox[0]["why"], "version")
	assert_contains(net.last_error, "version")
	net.close("")


func test_local_addresses_are_private_only() -> void:
	for a in _net().local_addresses():
		var p := str(a).split(".")
		var ok: bool = p[0] == "10" or (p[0] == "192" and p[1] == "168") or (p[0] == "172" and int(p[1]) >= 16 and int(p[1]) <= 31)
		assert_true(ok, str(a))


func test_two_links_can_really_talk_on_loopback() -> void:
	# a real ENet server and client in this one process, each with its own SceneMultiplayer
	var server_peer := ENetMultiplayerPeer.new()
	var port := 24790
	var err := server_peer.create_server(port, 1)
	assert_eq(err, OK, "the test port is free")
	if err != OK:
		return
	var client_peer := ENetMultiplayerPeer.new()
	assert_eq(client_peer.create_client("127.0.0.1", port), OK)
	var deadline := Time.get_ticks_msec() + 4000
	while client_peer.get_connection_status() != MultiplayerPeer.CONNECTION_CONNECTED and Time.get_ticks_msec() < deadline:
		server_peer.poll()
		client_peer.poll()
		OS.delay_msec(5)
	assert_eq(client_peer.get_connection_status(), MultiplayerPeer.CONNECTION_CONNECTED)
	server_peer.close()
	client_peer.close()


# --- the scene -------------------------------------------------------------------------------------------------------------------------

func test_the_scene_plays_a_duel_in_virtual_time() -> void:
	_setup()
	OS.set_environment("RW_DUEL_VIRTUAL", "1")
	OS.set_environment("RW_DUEL_SOLO", "1")
	OS.set_environment("RW_DUEL_BOT", "perfect")
	OS.set_environment("RW_DUEL_SKILL", "apprentice")
	OS.set_environment("RW_DUEL_SEED", "21")
	var host := Control.new()
	host.size = Vector2(1280, 720)
	tree.root.add_child(host)
	var scene: DuelPlay = (load("res://src/duel/duel_play.tscn") as PackedScene).instantiate()
	host.add_child(scene)
	assert_true(scene.solo)
	assert_eq(scene.phase, "countdown")
	assert_true(scene.engine.level.notes.size() > 0)
	assert_eq(scene.stage.names[1], "The Apprentice")
	var t := -scene.engine.count_in_s()
	while not scene.duel.finished and t < 200.0:
		t += 1.0 / 30.0
		scene._advance(t, t)
	assert_true(scene.duel.finished, "the duel ended")
	assert_eq(scene.duel.winner, 0, "a perfect player beats the apprentice")
	assert_eq(scene.duel.hp10[1], 0)
	assert_true(scene.engine.stopped, "no more phrases once it is over")
	assert_true(scene.trace.any(func(e: Dictionary) -> bool: return e["kind"] == "end"))
	assert_true(scene.stage.pending_spells() > 0 or scene.stage.hp_shown10(1) <= _rules.max_hp10(), "the stage was told about the spells")
	host.queue_free()
	for k in ["RW_DUEL_VIRTUAL", "RW_DUEL_SOLO", "RW_DUEL_BOT", "RW_DUEL_SKILL", "RW_DUEL_SEED"]:
		OS.set_environment(k, "")


func test_the_lobby_builds() -> void:
	var host := Control.new()
	host.size = Vector2(1280, 720)
	tree.root.add_child(host)
	var lobby: DuelLobby = (load("res://src/duel/duel_lobby.tscn") as PackedScene).instantiate()
	host.add_child(lobby)
	assert_true(lobby._wifi_box != null)
	assert_true(lobby._name_edit.text != "")
	var buttons := 0
	for c in lobby.find_children("*", "Button", true, false):
		buttons += 1
	assert_true(buttons >= 5, "back, three rivals, host and join: %d" % buttons)
	host.queue_free()
	_net().stop_browsing()
