extends TestCase
## Blackjack rules: hand values, deck, deal, turns, NPC and dealer policy, results, payouts, determinism.


func _c(rank: int, suit: int = 0) -> Dictionary:
	return {"rank": rank, "suit": suit}


func _ranks(list: Array) -> Array:
	var out: Array = []
	for i in list.size():
		out.append(_c(int(list[i]), i % 4))
	return out


## Game with an exact deal: each seat's two cards (dealer: [up, down]) then `extra` draws in order.
func _game(npc_a: Array, player: Array, npc_b: Array, dealer: Array, extra: Array = []) -> BlackjackGame:
	var order: Array = [npc_a[0], player[0], npc_b[0], dealer[0], npc_a[1], player[1], npc_b[1], dealer[1]]
	order.append_array(extra)
	return BlackjackGame.new(1, BlackjackDeck.stacked(_ranks(order), 99))


## Plain filler hands: npc_a 10+7, npc_b 10+7 (both stand on 17).
func _simple(player: Array, dealer: Array, extra: Array = []) -> BlackjackGame:
	return _game([10, 7], player, [10, 7], dealer, extra)


func _run(g: BlackjackGame) -> void:
	g.start_hand()
	if g.state == "player_turn":
		g.stick()
	g.play_others()


func _kinds(events: Array) -> Array:
	var out: Array = []
	for e in events:
		out.append(e["kind"])
	return out


func _key(card: Dictionary) -> String:
	return "%d_%d" % [card["rank"], card["suit"]]


# hand_value

func test_hand_value_table() -> void:
	var cases := [
		[[1, 13], 21, true, false, true],
		[[1, 1], 12, true, false, false],
		[[1, 1, 9], 21, true, false, false],
		[[1, 5, 13], 16, false, false, false],
		[[1, 1, 1], 13, true, false, false],
		[[1, 1, 1, 1], 14, true, false, false],
		[[1, 1, 1, 1, 10], 14, false, false, false],
		[[10, 6, 9], 25, false, true, false],
		[[11, 12], 20, false, false, false],
		[[13, 5, 6], 21, false, false, false],
		[[2, 3], 5, false, false, false],
		[[1, 6], 17, true, false, false],
		[[1, 6, 10], 17, false, false, false],
		[[10, 1], 21, true, false, true],
		[[7, 7, 7], 21, false, false, false],
		[[1], 11, true, false, false],
		[[], 0, false, false, false],
	]
	for c in cases:
		var v := BlackjackGame.hand_value(_ranks(c[0]))
		assert_eq(v["total"], c[1], "total of %s" % str(c[0]))
		assert_eq(v["soft"], c[2], "soft of %s" % str(c[0]))
		assert_eq(v["bust"], c[3], "bust of %s" % str(c[0]))
		assert_eq(v["natural"], c[4], "natural of %s" % str(c[0]))


# payouts

func test_payouts() -> void:
	assert_eq(BlackjackGame.payout_pence(500, "blackjack"), 1250)
	assert_eq(BlackjackGame.payout_pence(500, "win"), 1000)
	assert_eq(BlackjackGame.payout_pence(500, "push"), 500)
	assert_eq(BlackjackGame.payout_pence(500, "lose"), 0)
	assert_eq(BlackjackGame.payout_pence(500, "bust"), 0)
	assert_eq(BlackjackGame.payout_pence(500, ""), 0)
	assert_eq(BlackjackGame.payout_pence(333, "blackjack"), 832, "integer division")
	assert_eq(BlackjackGame.payout_pence(333, "win"), 666)
	assert_eq(BlackjackGame.payout_pence(1, "blackjack"), 2)
	assert_eq(BlackjackGame.payout_pence(0, "blackjack"), 0)


# deck

func test_a_full_deck_has_52_unique_cards() -> void:
	var d := BlackjackDeck.new(7)
	assert_eq(d.remaining(), 52)
	var seen := {}
	for i in 52:
		seen[_key(d.draw())] = true
	assert_eq(seen.size(), 52)
	assert_eq(d.remaining(), 0)
	assert_eq(d.drawn_count(), 52)


func test_same_seed_same_order_different_seed_differs() -> void:
	var a := BlackjackDeck.new(5)
	var b := BlackjackDeck.new(5)
	var c := BlackjackDeck.new(6)
	var same := true
	var differs := false
	for i in 52:
		var x := _key(a.draw())
		if x != _key(b.draw()):
			same = false
		if x != _key(c.draw()):
			differs = true
	assert_true(same)
	assert_true(differs)


func test_rebuild_excludes_cards_in_play() -> void:
	var d := BlackjackDeck.new(3)
	for i in 52:
		d.draw()
	var table := [_c(1, 0), _c(13, 3), _c(5, 2)]
	var seen := {}
	for i in 49:
		var card := d.draw(table)
		assert_false(table.has(card), "never a card on the table")
		seen[_key(card)] = true
	assert_eq(seen.size(), 49, "the rest of the deck, each once")
	assert_eq(d.drawn_count(), 52 + 49)


func test_stacked_deck_deals_in_order_then_falls_back() -> void:
	var d := BlackjackDeck.stacked(_ranks([5, 9, 13]), 4)
	assert_eq(d.draw()["rank"], 5)
	assert_eq(d.draw()["rank"], 9)
	assert_eq(d.draw()["rank"], 13)
	assert_eq(d.remaining(), 0)
	var c := d.draw()
	assert_true(c["rank"] >= 1 and c["rank"] <= 13)
	assert_eq(d.remaining(), 51)


# deal and state machine

func test_deal_order_and_face_down_dealer_card() -> void:
	var g := _simple([9, 8], [6, 10])
	assert_true(g.start_hand())
	assert_eq(g.hand_number, 1)
	assert_eq(g.state, "player_turn")
	var deals := g.events.filter(func(e): return e["kind"] == "deal")
	assert_eq(deals.size(), 8)
	var seats: Array = []
	for e in deals:
		seats.append(e["seat"])
	assert_eq(seats, ["npc_a", "player", "npc_b", "dealer", "npc_a", "player", "npc_b", "dealer"])
	assert_true(deals[3]["face_up"])
	assert_false(deals[7]["face_up"])
	assert_eq(deals[7]["hand"], 1)
	assert_false(g.cards("dealer")[1]["face_up"])
	assert_eq(g.dealer_up_card()["rank"], 6)
	assert_eq(g.cards("player").size(), 2)
	assert_eq(g.value("player")["total"], 17)
	assert_eq(deals[5]["total"], 17, "running total on the event")
	assert_eq(deals[7]["total"], 6, "hidden card not counted in event total")
	assert_eq(g.value("dealer", true)["total"], 6)
	assert_eq(g.value("dealer")["total"], 16)


func test_player_out_is_dealt_nothing() -> void:
	var g := BlackjackGame.new(2)
	assert_true(g.start_hand(false))
	assert_eq(g.cards("player").size(), 0)
	assert_eq(g.cards("npc_a").size(), 2)
	assert_eq(g.cards("dealer").size(), 2)
	assert_eq(g.state, "others")
	assert_false(g.twist())
	assert_true(g.play_others())
	assert_eq(g.state, "done")
	assert_eq(g.result("player"), "")
	assert_true(g.result("npc_a") != "")
	assert_true(g.result("dealer") == "")


func test_wrong_state_calls_change_nothing() -> void:
	var g := _simple([9, 8], [10, 7])
	assert_false(g.twist(), "idle")
	assert_false(g.stick(), "idle")
	assert_false(g.play_others(), "idle")
	assert_false(g.clear_hand(), "idle")
	assert_false(g.abandon_hand(), "idle")
	assert_eq(g.events.size(), 0)
	g.start_hand()
	var ev := g.events.size()
	var snapshot := g.cards("player").size()
	for i in 20:
		assert_false(g.start_hand(), "hand in progress")
		assert_false(g.play_others(), "player turn")
		assert_false(g.clear_hand())
	assert_eq(g.events.size(), ev)
	assert_eq(g.cards("player").size(), snapshot)
	assert_eq(g.hand_number, 1)
	g.stick()
	ev = g.events.size()
	for i in 20:
		assert_false(g.twist())
		assert_false(g.stick())
		assert_false(g.start_hand())
	assert_eq(g.events.size(), ev)
	assert_eq(g.cards("player").size(), 2)
	g.play_others()
	ev = g.events.size()
	for i in 20:
		assert_false(g.twist())
		assert_false(g.stick())
		assert_false(g.play_others())
		assert_false(g.start_hand(), "done but not cleared")
	assert_eq(g.events.size(), ev)
	assert_eq(g.hand_number, 1)
	assert_true(g.clear_hand())
	assert_eq(g.state, "idle")
	assert_eq(g.cards("player").size(), 0)
	assert_true(g.start_hand())
	assert_eq(g.hand_number, 2)


func test_twist_and_stick_flow() -> void:
	var g := _simple([5, 6], [10, 8], [4])
	g.start_hand()
	assert_true(g.twist())
	assert_eq(g.value("player")["total"], 15)
	assert_eq(g.state, "player_turn")
	assert_true(g.stick())
	assert_eq(g.state, "others")
	assert_true(g.play_others())
	assert_eq(g.state, "done")
	assert_eq(g.result("player"), "lose", "15 against 18")


func test_twist_to_21_ends_the_turn() -> void:
	var g := _simple([5, 6], [10, 8], [10])
	g.start_hand()
	g.twist()
	assert_eq(g.value("player")["total"], 21)
	assert_eq(g.state, "others")
	assert_false(g.stick())


func test_bust_ends_turn_and_loses_even_if_dealer_busts() -> void:
	# player 10+6, hits 10 -> 26. dealer 10+6 then hits 10 -> 26.
	var g := _simple([10, 6], [10, 6], [10, 10])
	g.start_hand()
	g.twist()
	assert_eq(g.state, "others")
	assert_true(g.value("player")["bust"])
	assert_false(g.twist(), "no more twisting")
	g.play_others()
	assert_true(g.value("dealer")["bust"])
	assert_eq(g.result("player"), "bust")
	assert_eq(g.result("npc_a"), "win", "npcs stand on 17, dealer bust")
	var kinds := _kinds(g.events)
	assert_true(kinds.has("bust"))


# results

func test_natural_skips_turn_and_pays_blackjack() -> void:
	var g := _simple([1, 13], [10, 7])
	g.start_hand()
	assert_eq(g.state, "others", "turn skipped")
	assert_false(g.twist())
	assert_true(_kinds(g.events).has("natural"))
	g.play_others()
	assert_eq(g.result("player"), "blackjack")
	assert_eq(BlackjackGame.payout_pence(500, g.result("player")), 1250)


func test_natural_vs_natural_is_a_push() -> void:
	var g := _simple([1, 13], [1, 12])
	g.start_hand()
	g.play_others()
	assert_eq(g.result("player"), "push")


func test_dealer_natural_beats_three_card_21() -> void:
	var g := _simple([5, 6], [1, 13], [10])
	g.start_hand()
	g.twist()
	assert_eq(g.value("player")["total"], 21)
	g.play_others()
	assert_eq(g.result("player"), "lose")
	assert_eq(g.result("npc_a"), "lose")


func test_push_win_lose() -> void:
	var g := _simple([10, 8], [10, 8])
	_run(g)
	assert_eq(g.result("player"), "push")
	g = _simple([10, 9], [10, 8])
	_run(g)
	assert_eq(g.result("player"), "win")
	g = _simple([10, 7], [10, 9])
	_run(g)
	assert_eq(g.result("player"), "lose")
	assert_eq(g.result("npc_a"), "lose")


func test_result_only_in_done() -> void:
	var g := _simple([10, 9], [10, 8])
	assert_eq(g.result("player"), "")
	g.start_hand()
	assert_eq(g.result("player"), "")
	g.stick()
	g.play_others()
	assert_eq(g.result("player"), "win")
	g.clear_hand()
	assert_eq(g.result("player"), "")


# dealer and NPC policy

func test_dealer_hits_16() -> void:
	var g := _simple([10, 9], [10, 6], [5])
	_run(g)
	assert_eq(g.cards("dealer").size(), 3)
	assert_eq(g.value("dealer")["total"], 21)
	assert_true(g.cards("dealer")[1]["face_up"])
	assert_true(_kinds(g.events).has("reveal"))


func test_dealer_stands_on_hard_17() -> void:
	var g := _simple([10, 9], [10, 7], [2])
	_run(g)
	assert_eq(g.cards("dealer").size(), 2)


func test_dealer_stands_on_soft_17() -> void:
	var g := _simple([10, 9], [1, 6], [2])
	_run(g)
	assert_eq(g.cards("dealer").size(), 2)
	assert_true(g.value("dealer")["soft"])
	assert_eq(g.result("player"), "win")


func test_dealer_hits_soft_16_and_under() -> void:
	var g := _simple([10, 9], [1, 5], [10, 9])
	_run(g)
	# soft 16 hits a 10 (hard 16), hits again and busts on the 9
	assert_eq(g.cards("dealer").size(), 4)
	assert_true(g.value("dealer")["bust"])


func test_npc_hits_under_12() -> void:
	# npc_a 5+6 = 11 hits the 3 -> 14, dealer up 10 so hits again.
	var g := _game([5, 6], [10, 9], [10, 7], [10, 7], [3, 4])
	_run(g)
	assert_eq(g.value("npc_a")["total"], 18)
	assert_eq(g.cards("npc_a").size(), 4)


func test_npc_hard_12_to_16_depends_on_dealer_up_card() -> void:
	# dealer up 7: hit. 10+6 + 5 = 21
	var g := _game([10, 6], [10, 9], [10, 7], [7, 10], [5])
	_run(g)
	assert_eq(g.cards("npc_a").size(), 3)
	# dealer up 6: stand
	g = _game([10, 6], [10, 9], [10, 7], [6, 10], [5])
	_run(g)
	assert_eq(g.cards("npc_a").size(), 2)
	# dealer up 10 hits; up ace counts as 11 and hits
	g = _game([10, 2], [10, 9], [10, 7], [13, 7], [9])
	_run(g)
	assert_eq(g.cards("npc_a").size(), 3)
	g = _game([10, 2], [10, 9], [10, 7], [1, 6], [9])
	_run(g)
	assert_eq(g.cards("npc_a").size(), 3)
	# up 2..6 all stand
	for up in [2, 3, 4, 5, 6]:
		g = _game([10, 2], [10, 9], [10, 7], [up, 10], [3])
		_run(g)
		assert_eq(g.cards("npc_a").size(), 2, "stands against %d" % up)


func test_npc_soft_totals() -> void:
	# soft 17 hits even against a 2 up: A+6, draws 4 -> soft 21
	var g := _game([1, 6], [10, 9], [10, 7], [2, 10], [4])
	_run(g)
	assert_eq(g.cards("npc_a").size(), 3)
	assert_eq(g.value("npc_a")["total"], 21)
	# soft 18 stands
	g = _game([1, 7], [10, 9], [10, 7], [10, 7], [4])
	_run(g)
	assert_eq(g.cards("npc_a").size(), 2)
	# hard 17 stands against an ace
	g = _game([10, 7], [10, 9], [10, 7], [1, 6], [4])
	_run(g)
	assert_eq(g.cards("npc_a").size(), 2)


func test_npc_natural_stands() -> void:
	var g := _game([1, 13], [10, 9], [10, 7], [10, 7], [4])
	_run(g)
	assert_eq(g.cards("npc_a").size(), 2)
	assert_eq(g.result("npc_a"), "blackjack")


func test_npc_bust() -> void:
	var g := _game([10, 6], [10, 9], [10, 7], [10, 7], [10])
	_run(g)
	assert_eq(g.result("npc_a"), "bust")


# abandon

func test_abandon_mid_turn_returns_to_idle() -> void:
	var g := BlackjackGame.new(8)
	g.start_hand()
	g.twist()
	assert_true(g.abandon_hand())
	assert_eq(g.state, "idle")
	assert_eq(g.cards("player").size(), 0)
	assert_eq(g.result("player"), "")
	assert_true(g.start_hand())
	assert_eq(g.hand_number, 2)
	assert_eq(g.cards("player").size(), 2)


func test_abandon_in_others_state() -> void:
	var g := BlackjackGame.new(8)
	g.start_hand(false)
	assert_true(g.abandon_hand())
	assert_eq(g.state, "idle")


# events

func test_drain_events() -> void:
	var g := _simple([10, 9], [10, 8])
	g.start_hand()
	var e := g.drain_events()
	assert_eq(e.size(), 8)
	assert_eq(g.events.size(), 0)
	g.stick()
	g.play_others()
	var kinds := _kinds(g.drain_events())
	assert_eq(kinds[0], "stand")
	assert_true(kinds.has("reveal"))
	assert_eq(kinds.count("result"), 3)
	assert_eq(kinds[kinds.size() - 1], "result")


func test_result_event_fields() -> void:
	var g := _simple([10, 9], [10, 8])
	_run(g)
	var r := g.events.filter(func(e): return e["kind"] == "result" and e["seat"] == "player")
	assert_eq(r.size(), 1)
	assert_eq(r[0]["result"], "win")
	assert_eq(r[0]["total"], 19)
	assert_eq(r[0]["dealer_total"], 18)


# determinism and long play

func _refuse(g: BlackjackGame) -> void:
	for i in 5:
		if g.state != "player_turn":
			g.twist()
			g.stick()
		if g.state != "idle":
			g.start_hand()
		if g.state != "others":
			g.play_others()
		if g.state != "done":
			g.clear_hand()
		if g.state == "idle":
			g.abandon_hand()


func _play_session(seed: int, hands: int, noise: bool) -> Array:
	var g := BlackjackGame.new(seed)
	var all: Array = []
	for h in hands:
		if noise:
			_refuse(g)
		g.start_hand(h % 5 != 4)
		if noise:
			_refuse(g)
		while g.state == "player_turn":
			if g.value("player")["total"] < 15:
				g.twist()
			else:
				g.stick()
			if noise:
				_refuse(g)
		g.play_others()
		if noise:
			_refuse(g)
		all.append_array(g.drain_events())
		g.clear_hand()
		all.append_array(g.drain_events())
	return all


func test_same_seed_same_events_different_seed_differs() -> void:
	assert_eq(_play_session(11, 12, false), _play_session(11, 12, false))
	assert_true(_play_session(11, 12, false) != _play_session(12, 12, false))


func test_refused_actions_do_not_disturb_the_stream() -> void:
	assert_eq(_play_session(21, 15, false), _play_session(21, 15, true))


func test_deck_exhaustion_over_many_hands() -> void:
	var g := BlackjackGame.new(31)
	for h in 60:
		assert_true(g.start_hand())
		while g.state == "player_turn":
			if g.value("player")["total"] < 16:
				g.twist()
			else:
				g.stick()
		g.play_others()
		assert_eq(g.state, "done")
		var seen := {}
		var count := 0
		for seat in BlackjackGame.SEATS:
			for c in g.cards(seat):
				seen[_key(c)] = true
				count += 1
		assert_eq(seen.size(), count, "no duplicate card on the table, hand %d" % h)
		assert_true(g.result("player") != "")
		g.clear_hand()
	# 60 hands of at least 8 cards is at least 480 draws: the deck was rebuilt many times without a failure


func test_mid_hand_rebuild_never_duplicates() -> void:
	# Leave 3 cards in the deck so the rebuild lands in the middle of a hand.
	var deck := BlackjackDeck.new(40)
	for i in 49:
		deck.draw()
	var g := BlackjackGame.new(40, deck)
	for h in 30:
		g.start_hand()
		g.stick()
		g.play_others()
		var seen := {}
		var count := 0
		for seat in BlackjackGame.SEATS:
			for c in g.cards(seat):
				seen[_key(c)] = true
				count += 1
		assert_eq(seen.size(), count, "hand %d" % h)
		g.clear_hand()
