extends TestCase
## The card table staged in the room (package A8b, CONTRACTS.md 10, ruling 38), without the stage: the activity's things, people and feedback as data, through the recording
## WorldThings port. Every dealt card is a thing on the felt (sliding from the deck, then at its seat's spot, face or back as the game says); the player's own chip stack is the
## wallet's balance and the bet pile the held stake at every frame; the three other people are directed only into the six people states, at song times that do not depend
## on the frame rate; a winning hand's cards get a tick, a bust a cross, a payout a glow on the stack; the controls are four pictograms in the pad slots. (Replaces
## test_blackjack_visual_state.gd, which checked the same money rules on the close-up's drawing.)

const BEAT := 60.0 / 174.0
const CONFIG_PATH := "res://content/minigames/blackjack.json"


func _cards(ranks: Array) -> Array:
	var out: Array = []
	for i in ranks.size():
		out.append({"rank": int(ranks[i]), "suit": i % 4})
	return out


func _deal(player: Array, dealer: Array, extra: Array = [], npc_a: Array = [10, 7], npc_b: Array = [10, 7]) -> Array:
	var order: Array = [npc_a[0], player[0], npc_b[0], dealer[0], npc_a[1], player[1], npc_b[1], dealer[1]]
	order.append_array(extra)
	return _cards(order)


func _rig(cards: Array = [], seed := 7) -> Dictionary:
	var w := RunWallet.new()
	var port := WorldThings.new()
	var a := BlackjackActivity.new()
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	var ctx := {"wallet": w, "seed": seed, "beat_s": BEAT, "config": cfg, "world": port}
	if not cards.is_empty():
		ctx["deck"] = BlackjackDeck.stacked(cards, 99)
	a.setup(ctx)
	return {"a": a, "w": w, "port": port, "t": 0.0}


func _thing(arr: Array, id: String) -> Dictionary:
	for x: Dictionary in arr:
		if str(x["id"]) == id:
			return x
	return {}


func _step(rig: Dictionary, dt := 1.0 / 60.0) -> void:
	rig["t"] = float(rig["t"]) + dt
	(rig["a"] as BlackjackActivity).update(float(rig["t"]))


func _until(rig: Dictionary, phase: String, max_s := 30.0) -> bool:
	var end := float(rig["t"]) + max_s
	while float(rig["t"]) < end:
		if str((rig["a"] as BlackjackActivity).state()["phase"]) == phase:
			return true
		_step(rig)
	return false


## Every frame: the stacks follow the wallet, every card dealt and landed stands at its seat's spot with the frame the game says, every card in flight is between the deck and its spot.
func _check_frame(rig: Dictionary, bad: Array) -> void:
	var a: BlackjackActivity = rig["a"]
	var w: RunWallet = rig["w"]
	var s := a.state()
	var arr := a.things()
	var phase := str(s["phase"])
	var me := _thing(arr, "bj_chips_player")
	var bet := _thing(arr, "bj_bet")
	if me.is_empty() or bet.is_empty():
		bad.append("no stacks at %.3f" % float(rig["t"]))
		return
	if phase not in ["sitting", "leaving"]:
		if int(me["frame"]) != BlackjackActivity.chip_frame(w.balance_pence(), 0):
			bad.append("the player's stack %d is not the wallet %d at %.3f" % [int(me["frame"]), w.balance_pence(), float(rig["t"])])
	if int(bet["frame"]) != BlackjackActivity.chip_frame(w.held_pence(), 3):
		bad.append("the bet pile %d is not the stake %d at %.3f" % [int(bet["frame"]), w.held_pence(), float(rig["t"])])
	var st: Dictionary = BlackjackActivity.STAGING
	for seat: String in BlackjackActivity.SEATS:
		var cards: Array = s["seats"][seat]["cards"]
		for i in cards.size():
			var c: Dictionary = cards[i]
			var th := _thing(arr, BlackjackActivity.card_id(seat, i))
			var t := float(rig["t"])
			var dealt := t >= float(c["t_deal"]) and (float(c["t_clear"]) < 0.0 or t < float(c["t_clear"]) + 1.0 * BEAT)
			if dealt != not th.is_empty():
				bad.append("card %s %d: dealt %s but thing %s at %.3f" % [seat, i, str(dealt), str(not th.is_empty()), t])
				continue
			if th.is_empty():
				continue
			if str(th["sprite"]) != BlackjackActivity.CARDS or str(th["sector"]) != "dayroom":
				bad.append("card %s %d sheet or sector" % [seat, i])
			var landed := t >= float(c["t_land"]) and float(c["t_clear"]) < 0.0
			if landed:
				var x := float((st["cards_x"] as Dictionary)[seat]) + float(i) * float(st["fan"])
				if absf(float(th["at"][0]) - x) > 1e-4:
					bad.append("card %s %d not at its spot (%.3f vs %.3f)" % [seat, i, float(th["at"][0]), x])
				var want := BlackjackActivity.card_frame(c, bool(c["face_up"]))
				if int(th["frame"]) != want:
					bad.append("card %s %d frame %d, the game says %d" % [seat, i, int(th["frame"]), want])


func test_before_the_seat_nothing_then_the_deck_and_the_stacks_and_the_pile_grows_out_of_the_pockets() -> void:
	var rig := _rig()
	var a: BlackjackActivity = rig["a"]
	assert_eq(a.things(), [], "nothing before the player sits")
	assert_true(a.make_view() == null, "no canvas view")
	a.begin(0.0)
	var arr := a.things()
	assert_eq(arr.map(func(x: Dictionary) -> String: return str(x["id"])), ["bj_deck", "bj_chips_player", "bj_chips_npc_a", "bj_chips_npc_b", "bj_bet"])
	assert_eq(int(_thing(arr, "bj_chips_player")["frame"]), BlackjackActivity.chip_frame(0, 0), "the pockets are not emptied yet")
	var seen: Array = []
	while float(rig["t"]) < 5.0 * BEAT:
		_step(rig)
		var f := int(_thing(a.things(), "bj_chips_player")["frame"])
		if seen.is_empty() or seen[-1] != f:
			seen.append(f)
	assert_true(seen.size() >= 3, "the stack grows chip by chip as the money comes out (%s)" % str(seen))
	assert_eq(seen[-1], BlackjackActivity.chip_frame(2000, 0), "and stands at the wallet: four chips")
	for x: Dictionary in a.things():
		assert_true(x.has_all(["id", "sprite", "at", "sector", "size", "frame", "y"]), "a thing has the contract's keys: %s" % str(x["id"]))


func test_four_hands_every_card_is_a_thing_on_the_felt_and_the_stacks_follow_the_wallet_every_frame() -> void:
	var rig := _rig([], 11)
	var a: BlackjackActivity = rig["a"]
	a.begin(0.0)
	var bad: Array = []
	var hands := 0
	var steps := 0
	while steps < 60000:
		steps += 1
		var ph := str(a.state()["phase"])
		if hands >= 4 and ph == "await_bet":
			break
		if ph == "await_bet":
			a.tap("bet", float(rig["t"]))
			if hands % 2 == 1:
				a.tap("bet", float(rig["t"]))  # two steps every other hand
			hands += 1
		elif ph == "player_turn" and int(a.state()["seats"]["player"]["total"]) > 0:
			var tot := int(a.state()["seats"]["player"]["total"])
			a.tap("deck" if tot < 13 else "hand", float(rig["t"]))
		elif ph == "broke":
			break
		_step(rig)
		_check_frame(rig, bad)
	assert_true(hands >= 4, "four hands played (%d)" % hands)
	assert_eq(bad.slice(0, 8), [], "every frame")
	assert_eq((rig["w"] as RunWallet).held_pence(), 0)


func test_a_bust_crosses_the_card_that_busted_and_a_win_ticks_every_card_and_glows_the_stack() -> void:
	var rig := _rig(_deal([10, 6], [10, 7], [9]))
	var a: BlackjackActivity = rig["a"]
	var port: WorldThings = rig["port"]
	a.begin(0.0)
	_until(rig, "await_bet")
	a.tap("bet", float(rig["t"]))
	_until(rig, "player_turn")
	a.tap("deck", float(rig["t"]))
	_until(rig, "await_bet", 40.0)
	var crosses := port.feedback_log.filter(func(f: Dictionary) -> bool: return str(f["kind"]) == "cross")
	assert_eq(crosses.size(), 1, "one cross")
	assert_eq(str(crosses[0]["thing"]), BlackjackActivity.card_id("player", 2), "on the card that went over")
	assert_eq(a.feedback_log, port.feedback_log, "the activity's own log is what the room was asked")
	var r2 := _rig(_deal([10, 9], [10, 7]))
	var b: BlackjackActivity = r2["a"]
	b.begin(0.0)
	_until(r2, "await_bet")
	b.tap("bet", float(r2["t"]))
	_until(r2, "player_turn")
	b.tap("hand", float(r2["t"]))
	_until(r2, "await_bet", 40.0)
	var marks: Array = (r2["port"] as WorldThings).feedback_log.map(func(f: Dictionary) -> String: return "%s:%s" % [f["kind"], f["thing"]])
	assert_eq(marks, ["tick:bj_card_player_0", "tick:bj_card_player_1", "glow:bj_chips_player"], "a tick on each winning card, a glow on the stack the payout goes to")
	assert_eq((r2["w"] as RunWallet).balance_pence(), 2500)


func test_the_others_are_directed_only_into_the_six_people_states_at_frame_rate_free_times() -> void:
	var runs: Array = []
	for dt: float in [1.0 / 30.0, 1.0 / 60.0, 1.0 / 144.0]:
		var rig := _rig(_deal([10, 6], [10, 8], [5, 4, 3, 2]), 3)
		var a: BlackjackActivity = rig["a"]
		a.begin(0.0)
		var taps := [["bet", 5.0 * BEAT], ["hand", 12.0 * BEAT]]
		while float(rig["t"]) < 40.0 * BEAT:
			var nt := float(rig["t"]) + dt
			if not taps.is_empty() and nt >= float(taps[0][1]):  # (a tap lands at its own song time whatever the frame rate)
				nt = float(taps[0][1])
			rig["t"] = nt
			a.update(nt)
			if not taps.is_empty() and nt >= float(taps[0][1]):
				a.tap(str(taps[0][0]), nt)
				taps.pop_front()
		var log: Array = (rig["port"] as WorldThings).people_log
		for p: Dictionary in log:
			assert_true(str(p["id"]) in BlackjackActivity.ACTORS.values(), "a table player: %s" % str(p["id"]))
			assert_true(str(p["state"]) in BlackjackActivity.PEOPLE_STATES, "a people state: %s" % str(p["state"]))
		runs.append(log.map(func(p: Dictionary) -> String: return "%s:%s@%.4f" % [p["id"], p["state"], float(p["t0"])]))
	assert_true((runs[0] as Array).size() >= 6, "they act through the hand (%d directions)" % (runs[0] as Array).size())
	assert_eq(runs[1], runs[0], "60 fps directs the same, at the same song times, as 30")
	assert_eq(runs[2], runs[0], "and as 144")
	var states: Array = []
	for r: String in runs[0]:
		var st := r.split(":")[1].split("@")[0]
		if st not in states:
			states.append(st)
	for want in ["deal", "look", "happy"]:
		assert_true(want in states, "the hand has %s in it (%s)" % [want, str(states)])


func test_the_controls_are_four_pictograms_live_as_the_targets_are() -> void:
	var rig := _rig(_deal([10, 6], [10, 8]))
	var a: BlackjackActivity = rig["a"]
	var c := a.controls()
	assert_eq(c.map(func(x: Dictionary) -> String: return str(x["id"])), ["bet", "deck", "hand", "exit"])
	assert_eq(c.map(func(x: Dictionary) -> String: return str(x["pictogram"])), ["chip", "card_draw", "flat_hand", "door"], "a chip, a card being drawn, a flat hand, a door")
	for x: Dictionary in c:
		assert_eq(str(x["label"]), "", "no words")
		assert_true(str(x["pictogram"]) in ControlPictograms.SHAPES, "a known pictogram")
		assert_true((x["draw"] as Callable).is_valid(), "and it draws itself (lit as it is live)")
	a.begin(0.0)
	assert_false(a.control_live("bet"), "sitting: nothing")
	_until(rig, "await_bet")
	assert_true(a.control_live("bet") and a.control_live("exit"))
	assert_false(a.control_live("deck") or a.control_live("hand"))
	a.tap("bet", float(rig["t"]))
	_until(rig, "player_turn")
	assert_true(a.control_live("deck") and a.control_live("hand"))
	assert_false(a.control_live("bet"))


func test_the_things_are_gone_once_the_player_has_left() -> void:
	var rig := _rig()
	var a: BlackjackActivity = rig["a"]
	a.begin(0.0)
	_until(rig, "await_bet")
	a.tap("exit", float(rig["t"]))
	var shrink: Array = []
	while not a.is_done() and float(rig["t"]) < 20.0:
		_step(rig)
		var me := _thing(a.things(), "bj_chips_player")
		if not me.is_empty():
			shrink.append(int(me["frame"]))
	assert_true(a.is_done())
	assert_eq(a.things(), [], "nothing left on the table")
	assert_true(shrink.size() > 0 and shrink[0] >= shrink[-1], "the stack goes back into the pockets")
	assert_eq((rig["w"] as RunWallet).balance_pence(), 2000, "the wallet unchanged")
