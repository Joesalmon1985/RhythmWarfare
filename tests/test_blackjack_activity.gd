extends TestCase
## The blackjack activity (the director): phases, targets, money through a real RunWallet, leaving, interrupts, wobble, determinism across frame rates.

const BEAT := 60.0 / 174.0
const CONFIG_PATH := "res://content/minigames/blackjack.json"
const MOODS := ["neutral", "happy", "laugh", "surprised", "annoyed", "sad", "wince", "concerned", "smug", "thinking"]
const GESTURES := ["rest", "invite", "point_deck", "point_hand", "deal", "sweep", "pay", "shrug", "clap", "facepalm", "tap_table", "wave_off"]
const PLAYER_GESTURES := ["none", "pockets", "lay_money", "push_bet", "reach_deck", "cover_cards", "drop_cards", "empty_pockets", "gather_money"]
const GAZES := ["player", "deck", "own_cards", "dealer", "npc_a", "npc_b", "pile", "bet", "away"]
const SEATS := ["npc_a", "player", "npc_b", "dealer"]


# helpers

func _cards(ranks: Array) -> Array:
	var out: Array = []
	for i in ranks.size():
		out.append({"rank": int(ranks[i]), "suit": i % 4})
	return out


## An exact deal: npc_a, player, npc_b, dealer ([up, hole]); then `extra` draws in order.
func _deal(player: Array, dealer: Array, extra: Array = [], npc_a: Array = [10, 7], npc_b: Array = [10, 7]) -> Array:
	var order: Array = [npc_a[0], player[0], npc_b[0], dealer[0], npc_a[1], player[1], npc_b[1], dealer[1]]
	order.append_array(extra)
	return _cards(order)


func _rig(cards: Array = [], pence: int = 2000, seed: int = 7, start := true) -> Dictionary:
	var w := RunWallet.new()
	if pence < 2000:
		w.spend(2000 - pence)
	elif pence > 2000:
		w.add(pence - 2000)
	var a := BlackjackActivity.new()
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	var ctx := {"wallet": w, "seed": seed, "beat_s": BEAT, "config": cfg}
	if not cards.is_empty():
		ctx["deck"] = BlackjackDeck.stacked(cards, 99)
	a.setup(ctx)
	var rig := {"a": a, "w": w, "t": 0.0, "bad": [], "scan": false, "seen": {}}
	if start:
		a.begin(0.0)
	return rig


func _upd(rig: Dictionary, t: float) -> void:
	rig["t"] = t
	(rig["a"] as BlackjackActivity).update(t)
	if rig["scan"]:
		_scan(rig)


func _adv(rig: Dictionary, seconds: float, dt := 1.0 / 60.0) -> void:
	var end := float(rig["t"]) + seconds
	while float(rig["t"]) < end - 1e-9:
		_upd(rig, minf(float(rig["t"]) + dt, end))


## Advances until the phase is `phase` (true) or `max_s` seconds pass (false).
func _until(rig: Dictionary, phase: String, max_s := 60.0, dt := 1.0 / 60.0) -> bool:
	var end := float(rig["t"]) + max_s
	while float(rig["t"]) < end:
		if _phase(rig) == phase:
			return true
		_upd(rig, float(rig["t"]) + dt)
	return _phase(rig) == phase


## Bets, sticks when asked to act, and advances until the settling phase begins (the stake still held).
func _to_settling(rig: Dictionary) -> void:
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	if _phase(rig) == "player_turn":
		_tap(rig, "hand")
	_until(rig, "settling", 40.0)


## Advances until the settle step has fired (nothing held any more), at most 10 s.
func _to_settled(rig: Dictionary) -> void:
	var n := 0
	while _held(rig) > 0 and n < 500:
		_adv(rig, 0.02)
		n += 1


func _phase(rig: Dictionary) -> String:
	return String((rig["a"] as BlackjackActivity).state()["phase"])


func _tap(rig: Dictionary, target: String) -> bool:
	return (rig["a"] as BlackjackActivity).tap(target, float(rig["t"]))


func _st(rig: Dictionary) -> Dictionary:
	return (rig["a"] as BlackjackActivity).state()


func _bal(rig: Dictionary) -> int:
	return (rig["w"] as RunWallet).balance_pence()


func _held(rig: Dictionary) -> int:
	return (rig["w"] as RunWallet).held_pence()


func _sit(rig: Dictionary) -> void:
	_until(rig, "await_bet", 20.0)


## Bets and plays one hand to its end. `action`: "stick", "twist" (one card then stick if still on) or "none" (a natural needs no action).
func _play(rig: Dictionary, action := "stick") -> void:
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	if _phase(rig) == "player_turn":
		if action == "twist":
			_tap(rig, "deck")
			_adv(rig, 2.0 * BEAT)
			if _phase(rig) == "player_turn":
				_tap(rig, "hand")
		else:
			_tap(rig, "hand")
	var guard := 0
	while guard < 40 and _phase(rig) != "await_bet" and _phase(rig) != "broke":
		_adv(rig, 1.0)
		guard += 1


## Records every vocabulary name seen and flags snapshot inconsistencies into rig["bad"].
func _scan(rig: Dictionary) -> void:
	var s := _st(rig)
	var phase := String(s["phase"])
	for seat in SEATS:
		var p: Dictionary = s["seats"][seat]
		var mood := String(p["mood"]["name"])
		var gaze := String(p["gaze"]["target"])
		var gesture := String(p["gesture"]["name"])
		rig["seen"]["m:" + mood] = true
		rig["seen"]["g:" + gesture] = true
		if not (mood in MOODS):
			rig["bad"].append("mood " + mood)
		if not (gaze in GAZES):
			rig["bad"].append("gaze " + gaze)
		var allowed: Array = PLAYER_GESTURES if seat == "player" else GESTURES
		if not (gesture in allowed):
			rig["bad"].append("gesture %s on %s" % [gesture, seat])
	if phase != "sitting" and phase != "leaving":
		if int(s["pile"]["pence"]) != _bal(rig):
			rig["bad"].append("pile %d vs balance %d at %s" % [s["pile"]["pence"], _bal(rig), str(rig["t"])])
	if int(s["bet"]["pence"]) != _held(rig):
		rig["bad"].append("bet %d vs held %d" % [s["bet"]["pence"], _held(rig)])


func _stripped(s: Dictionary) -> Dictionary:
	var d := s.duplicate(true)
	d.erase("t")
	return d


func _player_cards(rig: Dictionary) -> Array:
	return _st(rig)["seats"]["player"]["cards"]


# sitting

func test_sitting_pile_and_no_targets() -> void:
	var rig := _rig()
	var a: BlackjackActivity = rig["a"]
	var s := a.state()
	assert_eq(s["phase"], "sitting")
	assert_eq(s["targets"], [])
	assert_eq(s["pile"]["from_pence"], 0)
	assert_eq(s["pile"]["pence"], 2000)
	assert_eq(s["pile"]["via"], "pockets")
	assert_eq(s["seats"]["player"]["gesture"]["name"], "pockets")
	_adv(rig, 1.0 * BEAT)
	assert_eq(a.targets(), [])
	assert_false(_tap(rig, "bet"), "no bet while sitting")
	assert_eq(_bal(rig), 2000)
	assert_eq(_held(rig), 0)
	_adv(rig, 2.5 * BEAT)
	assert_eq(_st(rig)["seats"]["player"]["gesture"]["name"], "lay_money")
	assert_true(_until(rig, "await_bet", 5.0))
	assert_eq(_st(rig)["targets"], ["bet", "exit"])
	assert_true(_st(rig)["hints"]["bet"])
	assert_eq(_bal(rig), 2000)
	assert_eq(_held(rig), 0)


func test_begin_with_400_goes_straight_to_broke() -> void:
	var rig := _rig([], 400)
	assert_eq(_phase(rig), "sitting")
	assert_true(_until(rig, "broke", 5.0))
	assert_eq(_st(rig)["targets"], ["exit"])
	assert_true(_st(rig)["hints"]["exit_urged"])
	assert_false(_tap(rig, "bet"))
	assert_eq(_bal(rig), 400)


# betting

func test_bet_holds_and_deals() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	assert_true(_tap(rig, "bet"))
	var s := _st(rig)
	assert_eq(s["phase"], "dealing")
	assert_eq(_bal(rig), 1500)
	assert_eq(_held(rig), 500)
	assert_eq(s["pile"]["pence"], 1500)
	assert_eq(s["pile"]["from_pence"], 2000)
	assert_eq(s["pile"]["via"], "bet")
	assert_eq(s["bet"]["pence"], 500)
	assert_eq(s["bet"]["via"], "pile")
	assert_eq(s["targets"], ["exit"])
	assert_eq(s["seats"]["player"]["gesture"]["name"], "push_bet")
	assert_eq(s["hand"], 1)
	for seat in SEATS:
		assert_eq(s["seats"][seat]["cards"].size(), 2, seat)
	assert_false(s["seats"]["dealer"]["cards"][1]["face_up"], "hole card down")
	assert_true(s["seats"]["npc_a"]["cards"][0]["t_deal"] > s["bet"]["t0"], "dealing starts after the bet moved")


func test_double_bet_tap_is_refused() -> void:
	var rig := _rig()
	_sit(rig)
	assert_true(_tap(rig, "bet"))
	assert_false(_tap(rig, "bet"))
	assert_eq(_held(rig), 500)
	assert_eq(_bal(rig), 1500)


func test_deal_order_and_times() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	_tap(rig, "bet")
	var s := _st(rig)
	var times: Array = []
	for seat in ["npc_a", "player", "npc_b", "dealer"]:
		times.append(s["seats"][seat]["cards"][0]["t_deal"])
	for seat in ["npc_a", "player", "npc_b", "dealer"]:
		times.append(s["seats"][seat]["cards"][1]["t_deal"])
	for i in range(1, times.size()):
		assert_near(float(times[i]) - float(times[i - 1]), 0.5 * BEAT, 1e-9, "one deal gap apart")
	assert_eq(s["seats"]["npc_a"]["total"], 0, "nothing has landed yet")
	assert_true(_until(rig, "player_turn", 20.0))
	s = _st(rig)
	assert_eq(s["seats"]["player"]["total"], 19)
	assert_eq(s["seats"]["dealer"]["total"], 10, "hole card not counted")


# the player's turn

func test_twist_adds_card_and_refuses_input_in_flight() -> void:
	var rig := _rig(_deal([5, 4], [10, 7], [3]))
	_sit(rig)
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	assert_eq(_st(rig)["targets"], ["deck", "hand", "exit"])
	assert_true(_tap(rig, "deck"))
	assert_eq(_player_cards(rig).size(), 3)
	assert_eq(_player_cards(rig)[2]["rank"], 3)
	assert_eq(_st(rig)["seats"]["player"]["gesture"]["name"], "reach_deck")
	assert_false(_tap(rig, "deck"), "in flight")
	assert_false(_tap(rig, "hand"), "in flight")
	assert_eq(_player_cards(rig).size(), 3)
	assert_eq(_st(rig)["targets"], ["exit"])
	_adv(rig, 1.2 * BEAT)
	assert_eq(_st(rig)["targets"], ["deck", "hand", "exit"])
	assert_eq(_st(rig)["seats"]["player"]["total"], 12)
	assert_eq(_phase(rig), "player_turn")


func test_stick_moves_on_and_late_taps_refused() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	assert_false(_tap(rig, "deck"), "deck before betting")
	assert_false(_tap(rig, "hand"), "hand before betting")
	_tap(rig, "bet")
	assert_false(_tap(rig, "deck"), "deck while dealing")
	assert_false(_tap(rig, "hand"), "hand while dealing")
	_until(rig, "player_turn", 20.0)
	assert_true(_tap(rig, "hand"))
	assert_eq(_phase(rig), "others")
	assert_eq(_st(rig)["seats"]["player"]["gesture"]["name"], "cover_cards")
	assert_false(_tap(rig, "hand"))
	assert_false(_tap(rig, "deck"))
	assert_false(_tap(rig, "bet"))
	assert_eq(_st(rig)["targets"], ["exit"])
	assert_false(_tap(rig, "nonsense"))


func test_tap_storm_changes_money_only_by_the_rules() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	rig["scan"] = true
	var changes: Array = [0]
	(rig["w"] as RunWallet).changed.connect(func(): changes[0] += 1)
	_sit(rig)
	var guard := 0
	while guard < 4000 and changes[0] < 2:
		for target in ["bet", "deck", "hand", "bogus", "bet"]:
			_tap(rig, target)
		_upd(rig, float(rig["t"]) + 1.0 / 60.0)
		guard += 1
	assert_eq(changes[0], 2, "one hold and one settle")
	assert_eq(_held(rig), 0)
	assert_true(_bal(rig) in [1500, 2000, 2500, 2750], "balance %d is a rule outcome" % _bal(rig))
	assert_eq(rig["bad"], [])


# results

func _result_case(player: Array, dealer: Array, extra: Array, action: String, expect_balance: int, expect_result: String) -> void:
	var rig := _rig(_deal(player, dealer, extra))
	rig["scan"] = true
	_sit(rig)
	_play(rig, action)
	assert_eq(_phase(rig), "await_bet", expect_result)
	assert_eq(_bal(rig), expect_balance, expect_result)
	assert_eq(_held(rig), 0, expect_result)
	assert_eq(_st(rig)["seats"]["player"]["result"], expect_result)
	assert_eq(rig["bad"], [], expect_result)
	assert_eq(_st(rig)["bet"]["pence"], 0)


func test_result_win() -> void:
	_result_case([10, 9], [10, 7], [], "stick", 2500, "win")


func test_result_blackjack() -> void:
	_result_case([1, 13], [10, 7], [], "none", 2750, "blackjack")


func test_result_push() -> void:
	_result_case([10, 7], [10, 7], [], "stick", 2000, "push")


func test_result_lose() -> void:
	_result_case([10, 6], [10, 8], [], "stick", 1500, "lose")


func test_result_bust_goes_through_others_and_settling() -> void:
	var rig := _rig(_deal([10, 6], [10, 7], [10]))
	_sit(rig)
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	assert_true(_tap(rig, "deck"))
	_adv(rig, 0.5 * BEAT)
	assert_eq(_phase(rig), "player_turn", "the card is still flying")
	_adv(rig, 1.0 * BEAT)
	assert_eq(_phase(rig), "others")
	assert_eq(_st(rig)["seats"]["player"]["gesture"]["name"], "drop_cards")
	assert_eq(_st(rig)["seats"]["player"]["total"], 26)
	assert_true(_until(rig, "settling", 30.0))
	assert_eq(_held(rig), 500, "not settled until the dealer collects")
	assert_true(_until(rig, "await_bet", 30.0))
	assert_eq(_bal(rig), 1500)
	assert_eq(_held(rig), 0)
	assert_eq(_st(rig)["seats"]["player"]["result"], "bust")


func test_player_natural_whole_table_reacts() -> void:
	var rig := _rig(_deal([1, 13], [10, 7]))
	_sit(rig)
	_tap(rig, "bet")
	var land := float(_st(rig)["seats"]["player"]["cards"][1]["t_land"])
	_upd(rig, land + 0.01)
	var s := _st(rig)
	for seat in ["npc_a", "npc_b", "dealer"]:
		assert_eq(s["seats"][seat]["mood"]["name"], "surprised", seat)
	assert_eq(s["seats"]["player"]["mood"]["name"], "happy")
	_upd(rig, land + 2.0 * BEAT)
	assert_eq(_st(rig)["seats"]["dealer"]["mood"]["name"], "happy")
	assert_true(_until(rig, "others", 20.0), "a natural skips the player's turn")


func test_npc_natural_laughs_or_is_happy() -> void:
	var rig := _rig(_deal([10, 9], [10, 7], [], [1, 13]))
	_sit(rig)
	_tap(rig, "bet")
	var land := float(_st(rig)["seats"]["npc_a"]["cards"][1]["t_land"])
	_upd(rig, land + 0.01)
	assert_true(_st(rig)["seats"]["npc_a"]["mood"]["name"] in ["happy", "laugh"])


func test_hole_card_flips_and_dealer_draws() -> void:
	var rig := _rig(_deal([10, 9], [10, 3], [5]))
	_sit(rig)
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	_tap(rig, "hand")
	var s := _st(rig)
	assert_eq(s["seats"]["dealer"]["cards"].size(), 3, "the dealer's draw is planned at once")
	var flip := float(s["seats"]["dealer"]["cards"][1]["t_flip"])
	assert_true(flip > float(rig["t"]))
	var draw := float(s["seats"]["dealer"]["cards"][2]["t_deal"])
	assert_true(draw > flip, "draws after the flip")
	_upd(rig, flip - 0.01)
	assert_false(_st(rig)["seats"]["dealer"]["cards"][1]["face_up"])
	_upd(rig, flip + 0.01)
	assert_true(_st(rig)["seats"]["dealer"]["cards"][1]["face_up"])
	assert_true(_until(rig, "await_bet", 40.0))
	assert_eq(_st(rig)["seats"]["player"]["result"], "win", "dealer 18 under 19")
	assert_eq(_bal(rig), 2500)
	for c in _st(rig)["seats"]["dealer"]["cards"]:
		assert_true(float(c["t_clear"]) >= 0.0, "cleared")


func test_settle_transitions() -> void:
	# win: pile from the old balance to the new, via the dealer; bet back to the pile
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	_to_settling(rig)
	_to_settled(rig)
	var s := _st(rig)
	assert_eq(s["pile"]["from_pence"], 1500)
	assert_eq(s["pile"]["pence"], 2500)
	assert_eq(s["pile"]["via"], "dealer")
	assert_eq(s["bet"]["from_pence"], 500)
	assert_eq(s["bet"]["pence"], 0)
	assert_eq(s["bet"]["via"], "pile")
	assert_eq(s["seats"]["dealer"]["gesture"]["name"], "pay")
	# lose: the bet goes to the dealer
	rig = _rig(_deal([10, 6], [10, 8]))
	_sit(rig)
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	_tap(rig, "hand")
	_until(rig, "settling", 30.0)
	_to_settled(rig)
	s = _st(rig)
	assert_eq(s["bet"]["via"], "dealer")
	assert_eq(s["seats"]["dealer"]["gesture"]["name"], "sweep")
	assert_eq(s["pile"]["pence"], 1500)
	# push: the stake returns via the bet spot
	rig = _rig(_deal([10, 7], [10, 7]))
	_sit(rig)
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	_tap(rig, "hand")
	_until(rig, "settling", 30.0)
	_to_settled(rig)
	s = _st(rig)
	assert_eq(s["pile"]["via"], "bet")
	assert_eq(s["pile"]["from_pence"], 1500)
	assert_eq(s["pile"]["pence"], 2000)


func test_blackjack_settle_mood_and_gesture() -> void:
	var rig := _rig(_deal([1, 13], [10, 7]))
	_sit(rig)
	_tap(rig, "bet")
	_until(rig, "settling", 40.0)
	_to_settled(rig)
	var s := _st(rig)
	assert_eq(s["seats"]["dealer"]["mood"]["name"], "surprised")
	assert_eq(s["seats"]["npc_a"]["mood"]["name"], "surprised")
	_adv(rig, 2.0 * BEAT)
	s = _st(rig)
	for n in ["npc_a", "npc_b"]:
		var laughing: bool = s["seats"][n]["mood"]["name"] == "laugh" or s["seats"][n]["gesture"]["name"] == "clap"
		assert_true(laughing, n)


func test_several_hands_in_a_row() -> void:
	var rig := _rig([], 2000, 11)
	rig["scan"] = true
	_sit(rig)
	var hands := 0
	for i in 5:
		if _phase(rig) != "await_bet":
			break
		_play(rig, "stick")
		hands += 1
	assert_true(hands >= 3)
	assert_eq(_st(rig)["hand"], hands)
	assert_eq(_held(rig), 0)
	assert_eq(rig["bad"], [])
	assert_true(rig["seen"].size() > 6, "a variety of moods and gestures appeared")


func test_vocabulary_over_many_outcomes() -> void:
	var cases := [
		[_deal([10, 9], [10, 7]), "stick"], [_deal([1, 13], [10, 7]), "none"], [_deal([10, 7], [10, 7]), "stick"],
		[_deal([10, 6], [10, 8]), "stick"], [_deal([10, 6], [10, 7], [10]), "twist"], [_deal([10, 9], [6, 4], [10], [10, 6], [9, 9]), "stick"],
		[_deal([10, 9], [10, 6], [10], [10, 6], [10, 5]), "stick"], [_deal([10, 8], [1, 13], []), "stick"],
	]
	for case in cases:
		var rig := _rig(case[0])
		rig["scan"] = true
		_sit(rig)
		_play(rig, case[1])
		assert_eq(rig["bad"], [])
		assert_eq(_held(rig), 0)


# money conservation

func test_conservation_over_40_hands() -> void:
	var w_bad: Array = []
	var total_hands := 0
	for hand_seed in range(1, 41):
		var rig := _rig([], 2000, hand_seed)
		rig["scan"] = true
		_sit(rig)
		var prev_total := _bal(rig) + _held(rig)
		var played := 0
		var guard := 0
		while played < 1 and guard < 6000:
			guard += 1
			var ph := _phase(rig)
			if ph == "await_bet":
				_tap(rig, "bet")
			elif ph == "player_turn":
				var tot := int(_st(rig)["seats"]["player"]["total"])
				_tap(rig, "deck" if tot < 15 else "hand")
			var a: BlackjackActivity = rig["a"]
			var before_held := _held(rig)
			_upd(rig, float(rig["t"]) + 1.0 / 30.0)
			var total := _bal(rig) + _held(rig)
			if total != prev_total:
				var res := String(_st(rig)["seats"]["player"]["result"])
				var expect := prev_total - 500 + BlackjackGame.payout_pence(500, res)
				if before_held != 500 or _held(rig) != 0 or total != expect:
					w_bad.append("seed %d: %d -> %d (result %s)" % [hand_seed, prev_total, total, res])
				prev_total = total
				played += 1
				total_hands += 1
			assert_true(a != null)
		_until(rig, "await_bet", 20.0)
		assert_eq(rig["bad"], [], "seed %d" % hand_seed)
	assert_eq(w_bad, [])
	assert_eq(total_hands, 40)


# broke

func test_losing_the_last_stake_goes_broke() -> void:
	var rig := _rig(_deal([10, 6], [10, 8]), 500)
	_sit(rig)
	assert_eq(_phase(rig), "await_bet")
	_play(rig, "stick")
	assert_eq(_bal(rig), 0)
	assert_eq(_phase(rig), "broke")
	assert_eq(_st(rig)["targets"], ["exit"])
	assert_false(_tap(rig, "bet"))
	assert_true(_st(rig)["hints"]["exit_urged"])
	assert_eq(_st(rig)["seats"]["player"]["gesture"]["name"], "empty_pockets")
	assert_eq(_st(rig)["seats"]["dealer"]["gesture"]["name"], "shrug")
	assert_eq(_st(rig)["seats"]["dealer"]["mood"]["name"], "concerned")
	assert_eq(_st(rig)["seats"]["npc_a"]["gaze"]["target"], "own_cards")
	assert_true(_tap(rig, "exit"))
	assert_eq(_phase(rig), "leaving")


# leaving

func test_leave_between_hands_changes_nothing() -> void:
	var rig := _rig()
	_sit(rig)
	assert_true(_tap(rig, "exit"))
	var s := _st(rig)
	assert_eq(s["phase"], "leaving")
	assert_eq(s["targets"], [])
	assert_eq(s["pile"]["pence"], 0)
	assert_eq(s["pile"]["from_pence"], 2000)
	assert_eq(s["pile"]["via"], "pockets")
	assert_eq(s["seats"]["player"]["gesture"]["name"], "gather_money")
	assert_eq(_bal(rig), 2000, "the wallet keeps the money")
	assert_false((rig["a"] as BlackjackActivity).is_done())
	_adv(rig, 2.0 * BEAT)
	assert_false((rig["a"] as BlackjackActivity).is_done())
	_adv(rig, 1.5 * BEAT)
	assert_true((rig["a"] as BlackjackActivity).is_done())
	assert_eq((rig["a"] as BlackjackActivity).done_reason(), "left")
	assert_eq(_bal(rig), 2000)
	assert_eq(_held(rig), 0)
	assert_true(_st(rig)["done"])


func test_leave_during_player_turn_forfeits_once() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	assert_true(_tap(rig, "exit"))
	assert_eq(_bal(rig), 1500)
	assert_eq(_held(rig), 0)
	assert_eq(_st(rig)["bet"]["via"], "dealer")
	assert_eq(_st(rig)["seats"]["dealer"]["gesture"]["name"], "sweep")
	(rig["a"] as BlackjackActivity).request_leave(float(rig["t"]))
	assert_false(_tap(rig, "exit"))
	(rig["a"] as BlackjackActivity).interrupt("fall", float(rig["t"]))
	_adv(rig, 5.0)
	assert_eq(_bal(rig), 1500)
	assert_eq(_held(rig), 0)
	assert_eq((rig["a"] as BlackjackActivity).done_reason(), "left")
	for seat in SEATS:
		for c in _st(rig)["seats"][seat]["cards"]:
			assert_true(float(c["t_clear"]) >= 0.0)


func test_leave_during_dealing_and_others_forfeits() -> void:
	for phase in ["dealing", "others"]:
		var rig := _rig(_deal([10, 9], [10, 7]))
		_sit(rig)
		_tap(rig, "bet")
		if phase == "others":
			_until(rig, "player_turn", 20.0)
			_tap(rig, "hand")
		assert_eq(_phase(rig), phase)
		assert_true(_tap(rig, "exit"))
		assert_eq(_bal(rig), 1500, phase)
		assert_eq(_held(rig), 0, phase)


func test_leave_after_settle_keeps_the_payout() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	_to_settling(rig)
	assert_eq(_held(rig), 500, "before the settle step the stake is still live")
	_to_settled(rig)
	assert_eq(_bal(rig), 2500)
	assert_true(_tap(rig, "exit"))
	_adv(rig, 5.0)
	assert_eq(_bal(rig), 2500, "payout stands, nothing forfeited or doubled")
	assert_eq(_held(rig), 0)
	assert_true((rig["a"] as BlackjackActivity).is_done())


func test_leave_in_settling_before_the_settle_step_forfeits() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	_to_settling(rig)
	assert_eq(_held(rig), 500)
	assert_true(_tap(rig, "exit"))
	_adv(rig, 6.0)
	assert_eq(_bal(rig), 1500)
	assert_eq(_held(rig), 0)


func test_request_leave_in_sitting() -> void:
	var rig := _rig()
	_adv(rig, 1.0 * BEAT)
	(rig["a"] as BlackjackActivity).request_leave(float(rig["t"]))
	assert_eq(_phase(rig), "leaving")
	_adv(rig, 4.0 * BEAT)
	assert_true((rig["a"] as BlackjackActivity).is_done())
	assert_eq(_bal(rig), 2000)


# interrupts

func test_fall_refunds_in_every_live_phase() -> void:
	for phase in ["dealing", "player_turn", "others"]:
		var rig := _rig(_deal([10, 9], [10, 7]))
		_sit(rig)
		_tap(rig, "bet")
		if phase != "dealing":
			_until(rig, "player_turn", 20.0)
		if phase == "others":
			_tap(rig, "hand")
		assert_eq(_phase(rig), phase)
		var a: BlackjackActivity = rig["a"]
		a.interrupt("fall", float(rig["t"]))
		assert_eq(_bal(rig), 2000, phase)
		assert_eq(_held(rig), 0, phase)
		var s := _st(rig)
		assert_eq(s["phase"], "falling")
		assert_eq(s["targets"], [])
		assert_eq(s["bet"]["via"], "pile")
		assert_eq(s["pile"]["via"], "bet")
		assert_eq(s["seats"]["npc_a"]["mood"]["name"], "surprised")
		assert_eq(s["seats"]["npc_a"]["gaze"]["target"], "player")
		_adv(rig, 3.0 * BEAT)
		assert_false(a.is_done(), phase)
		_adv(rig, 1.5 * BEAT)
		assert_true(a.is_done(), phase)
		assert_eq(a.done_reason(), "fall")
		assert_eq(_bal(rig), 2000)
		assert_eq(_held(rig), 0)
		assert_true(a.state()["seats"]["npc_a"]["mood"]["name"] in ["laugh", "concerned"])


func test_fall_after_settle_keeps_the_payout() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	_to_settling(rig)
	_to_settled(rig)
	(rig["a"] as BlackjackActivity).interrupt("fall", float(rig["t"]))
	_adv(rig, 6.0)
	assert_eq(_bal(rig), 2500)
	assert_eq(_held(rig), 0)
	assert_eq((rig["a"] as BlackjackActivity).done_reason(), "fall")


func test_run_over_refunds_and_finishes_at_once() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	_tap(rig, "bet")
	_until(rig, "player_turn", 20.0)
	var a: BlackjackActivity = rig["a"]
	a.interrupt("run_over", float(rig["t"]))
	assert_eq(_bal(rig), 2000)
	assert_eq(_held(rig), 0)
	assert_true(a.is_done())
	assert_eq(a.done_reason(), "run_over")
	a.interrupt("fall", float(rig["t"]))
	assert_eq(a.done_reason(), "run_over")
	var rig2 := _rig(_deal([10, 9], [10, 7]))
	_sit(rig2)
	_tap(rig2, "bet")
	(rig2["a"] as BlackjackActivity).interrupt("host", float(rig2["t"]))
	assert_true((rig2["a"] as BlackjackActivity).is_done())
	assert_eq((rig2["a"] as BlackjackActivity).done_reason(), "host")
	assert_eq(_bal(rig2), 2000)


func test_fall_between_hands_has_nothing_to_refund() -> void:
	var rig := _rig()
	_sit(rig)
	var changes: Array = [0]
	(rig["w"] as RunWallet).changed.connect(func(): changes[0] += 1)
	(rig["a"] as BlackjackActivity).interrupt("fall", float(rig["t"]))
	_adv(rig, 5.0)
	assert_eq(changes[0], 0)
	assert_eq(_bal(rig), 2000)
	assert_true((rig["a"] as BlackjackActivity).is_done())


func test_second_interrupt_changes_nothing() -> void:
	var rig := _rig(_deal([10, 9], [10, 7]))
	_sit(rig)
	_tap(rig, "bet")
	var changes: Array = [0]
	(rig["w"] as RunWallet).changed.connect(func(): changes[0] += 1)
	var a: BlackjackActivity = rig["a"]
	a.interrupt("fall", float(rig["t"]))
	a.interrupt("fall", float(rig["t"]))
	a.interrupt("run_over", float(rig["t"]) + 0.1)
	a.request_leave(float(rig["t"]) + 0.2)
	assert_eq(changes[0], 1)
	assert_eq(_bal(rig), 2000)
	assert_eq(_phase(rig), "falling")
	assert_false(a.is_done())
	_adv(rig, 5.0)
	assert_eq(a.done_reason(), "fall")


func test_interrupt_during_sitting() -> void:
	var rig := _rig()
	_adv(rig, 1.0 * BEAT)
	var a: BlackjackActivity = rig["a"]
	a.interrupt("fall", float(rig["t"]))
	assert_eq(_phase(rig), "falling")
	assert_eq(_bal(rig), 2000)
	_adv(rig, 5.0)
	assert_true(a.is_done())
	assert_eq(a.done_reason(), "fall")


func test_fall_while_leaving_keeps_leaving() -> void:
	var rig := _rig()
	_sit(rig)
	_tap(rig, "exit")
	(rig["a"] as BlackjackActivity).interrupt("fall", float(rig["t"]))
	assert_eq(_phase(rig), "leaving")
	_adv(rig, 5.0)
	assert_eq((rig["a"] as BlackjackActivity).done_reason(), "left")


# wobble

func test_wobble_touches_only_the_dealer_face() -> void:
	var cards := _deal([10, 9], [10, 7])
	var control := _rig(cards)
	var wob := _rig(cards)
	for r in [control, wob]:
		_sit(r)
		_tap(r, "bet")
		_until(r, "player_turn", 20.0)
	assert_eq(_stripped(_st(control)), _stripped(_st(wob)))
	(wob["a"] as BlackjackActivity).set_wobble(1, float(wob["t"]))
	var s := _st(wob)
	assert_eq(s["seats"]["dealer"]["mood"]["name"], "concerned")
	assert_eq(s["seats"]["dealer"]["gaze"]["target"], "player")
	assert_eq(s["wobble"]["level"], 1)
	for r in [control, wob]:
		_adv(r, 1.0)
		_tap(r, "hand")
	_adv(wob, 0.0)
	var sc := _st(control)
	var sw := _st(wob)
	for seat in SEATS:
		assert_eq(sw["seats"][seat]["cards"], sc["seats"][seat]["cards"], seat)
		assert_eq(sw["seats"][seat]["total"], sc["seats"][seat]["total"], seat)
	assert_eq(sw["phase"], sc["phase"])
	assert_eq(_bal(wob), _bal(control))
	assert_eq(_held(wob), _held(control))
	(wob["a"] as BlackjackActivity).set_wobble(0, float(wob["t"]))
	assert_eq(_st(wob)["wobble"]["level"], 0)
	for r in [control, wob]:
		_until(r, "await_bet", 40.0)
	assert_eq(_stripped(_st(control)["seats"]["npc_a"]), _stripped(_st(wob)["seats"]["npc_a"]))
	assert_eq(_st(wob)["seats"]["dealer"]["mood"], _st(control)["seats"]["dealer"]["mood"], "restored")
	assert_eq(_bal(wob), 2500)
	assert_eq(_bal(control), 2500)


# rhythm independence

func _full_cards(rig: Dictionary) -> Array:
	var out: Array = []
	var s := _st(rig)
	for seat in SEATS:
		var l: Array = []
		for c in s["seats"][seat]["cards"]:
			l.append([c["rank"], c["suit"]])
		out.append(l)
	return out


func test_rhythm_never_touches_the_cards() -> void:
	var a := _rig([], 2000, 31)
	var b := _rig([], 2000, 31)
	_sit(a)
	_sit(b)
	var seen_a: Array = []
	var seen_b: Array = []
	for i in 10:
		for r in [a, b]:
			if _phase(r) == "await_bet":
				_tap(r, "bet")
			_until(r, "player_turn", 20.0)
			if _phase(r) == "player_turn":
				var tot := int(_st(r)["seats"]["player"]["total"])
				_tap(r, "deck" if tot < 14 else "hand")
				if tot < 14:
					_adv(r, 1.1 * BEAT)
					if _phase(r) == "player_turn":
						_tap(r, "hand")
		var guard := 0
		while guard < 400 and not (_phase(a) == "await_bet" and _phase(b) == "await_bet") and _phase(a) != "broke":
			# b gets rhythm noise, refused taps and wobble toggles
			(b["a"] as BlackjackActivity).set_wobble(guard % 2, float(b["t"]))
			_tap(b, "deck" if _phase(b) == "await_bet" else "bet")
			_tap(b, "bogus")
			for r in [a, b]:
				_upd(r, float(r["t"]) + 0.25)
			guard += 1
		seen_a.append(_full_cards(a))
		seen_b.append(_full_cards(b))
		if _phase(a) != "await_bet":
			break
	assert_true(seen_a.size() >= 5)
	assert_eq(seen_a, seen_b)
	assert_eq(_bal(a), _bal(b))


# determinism across frame rates

func _run_script(steps: Array, taps: Array, checkpoints: Array, end: float) -> Dictionary:
	var rig := _rig([], 2000, 5)
	var history: Array = []
	var w: RunWallet = rig["w"]
	w.changed.connect(func(): history.append([w.balance_pence(), w.held_pence()]))
	var events: Array = []
	for t in checkpoints:
		events.append([float(t), "check", ""])
	for tp in taps:
		events.append([float(tp[0]), "tap", String(tp[1])])
	events.sort_custom(func(x, y): return x[0] < y[0] if x[0] != y[0] else (x[1] == "tap" and y[1] != "tap"))
	var t := 0.0
	var i := 0
	var step_i := 0
	var snaps := {}
	var a: BlackjackActivity = rig["a"]
	while t < end:
		var dt := float(steps[step_i % steps.size()])
		step_i += 1
		var nt := t + dt
		var hit := false
		if i < events.size() and float(events[i][0]) <= nt:
			nt = float(events[i][0])
			hit = true
		t = nt
		a.update(t)
		while hit and i < events.size() and float(events[i][0]) <= t:
			var e: Array = events[i]
			i += 1
			if e[1] == "tap":
				a.tap(String(e[2]), t)
			else:
				snaps[float(e[0])] = _stripped(a.state())
	return {"snaps": snaps, "history": history, "final": _stripped(a.state())}


func test_same_snapshot_at_any_frame_rate() -> void:
	var taps := [[4.0, "bet"], [4.0, "bet"], [9.0, "deck"], [9.1, "deck"], [11.0, "hand"], [30.0, "bet"], [35.0, "hand"], [36.0, "deck"], [60.0, "bet"], [64.0, "deck"], [66.0, "hand"], [95.0, "exit"]]
	var checkpoints: Array = []
	for k in range(1, 130):
		checkpoints.append(float(k) * 0.75)
	var ref := _run_script([1.0 / 60.0], taps, checkpoints, 100.0)
	assert_true(ref["history"].size() >= 2, "the script placed a bet")
	var patterns := [[1.0 / 30.0], [1.0 / 144.0], [0.011, 0.047, 0.02, 0.1, 0.0333, 0.3]]
	for p in patterns:
		var other := _run_script(p, taps, checkpoints, 100.0)
		assert_eq(other["history"], ref["history"], "wallet history")
		assert_eq(other["final"], ref["final"], "final")
		var bad := 0
		for k in ref["snaps"]:
			if other["snaps"].get(k, null) != ref["snaps"][k]:
				bad += 1
		assert_eq(bad, 0, "snapshots that differ for step %s" % str(p[0]))
		assert_eq(other["snaps"].size(), ref["snaps"].size())


# returning

func test_returning_starts_with_the_kept_balance() -> void:
	var rig := _rig(_deal([10, 6], [10, 8]))
	_sit(rig)
	_play(rig, "stick")
	assert_eq(_bal(rig), 1500)
	_tap(rig, "exit")
	_adv(rig, 5.0)
	assert_true((rig["a"] as BlackjackActivity).is_done())
	var w: RunWallet = rig["w"]
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	var b := BlackjackActivity.new()
	b.setup({"wallet": w, "seed": 3, "beat_s": BEAT, "config": cfg})
	b.begin(100.0)
	var s := b.state()
	assert_eq(s["phase"], "sitting")
	assert_eq(s["pile"]["from_pence"], 0)
	assert_eq(s["pile"]["pence"], 1500)
	assert_eq(s["pile"]["via"], "pockets")
	assert_false(b.is_done())
	b.update(100.0 + 5.0)
	assert_eq(b.state()["phase"], "await_bet")


func test_null_wallet_behaves_as_empty() -> void:
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	var a := BlackjackActivity.new()
	a.setup({"wallet": null, "seed": 1, "beat_s": BEAT, "config": cfg})
	a.begin(0.0)
	a.update(5.0)
	assert_eq(a.state()["phase"], "broke")
	assert_false(a.tap("bet", 5.0))


# config

func test_config_file() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	assert_eq(typeof(parsed), TYPE_DICTIONARY)
	var d: Dictionary = parsed
	assert_eq(d["id"], "blackjack")
	assert_eq(int(d["stake_pence"]), 500)
	assert_eq(int(d["wobble_at"]), 2)
	assert_eq(int(d["fall_at"]), 3)
	assert_true(d.has("timing_beats"))
	for k in BlackjackActivity.DEFAULT_TIMING:
		assert_true(d["timing_beats"].has(k), "timing_beats has " + str(k))
	var script: Variant = load(str(d["script"]))
	assert_true(script is GDScript)
	assert_true((script as GDScript).new() is MinigameActivity)
	var view: Control = BlackjackActivity.new().make_view()
	assert_true(view is BlackjackView, "the activity makes its table view")
	view.free()


# exits while seated: the room's ways out as doors (MinigameActivity "exits")

const ROOM_EXITS := [
	{"id": "r.exit_art", "route": "r.art", "scene": "art", "world": "w", "dir": "right", "default": true},
	{"id": "r.exit_dorm", "route": "r.dorm", "scene": "dorm", "world": "w", "dir": "up", "default": false},
	{"id": "r.exit_yard", "route": "r.yard", "scene": "courtyard", "world": "w", "dir": "left", "default": false},
	{"id": "r.exit_lab", "route": "r.lab", "scene": "nowhere", "world": "w2", "dir": "up", "default": false},
]


func _rig_x(n: int, cards: Array = [], pence: int = 2000, seed: int = 7) -> Dictionary:
	var w := RunWallet.new()
	if pence < 2000:
		w.spend(2000 - pence)
	var a := BlackjackActivity.new()
	var cfg: Variant = JSON.parse_string(FileAccess.get_file_as_string(CONFIG_PATH))
	var ctx := {"wallet": w, "seed": seed, "beat_s": BEAT, "config": cfg, "exits": ROOM_EXITS.slice(0, n)}
	if not cards.is_empty():
		ctx["deck"] = BlackjackDeck.stacked(cards, 99)
	a.setup(ctx)
	a.begin(0.0)
	return {"a": a, "w": w, "t": 0.0, "bad": [], "scan": false, "seen": {}}


func _doors(n: int) -> Array:
	var out: Array = []
	for e in ROOM_EXITS.slice(0, n):
		out.append("exit:" + str(e["route"]))
	return out


func test_one_exit_target_per_door_in_every_phase_with_0_1_2_and_4_exits() -> void:
	for n in [0, 1, 2, 4]:
		var doors := _doors(n) if n > 0 else ["exit"]
		var rig := _rig_x(n, _deal([10, 9], [10, 7], [5, 5, 5]))
		assert_eq(_st(rig)["targets"], [], "nothing while sitting (%d exits)" % n)
		_sit(rig)
		assert_eq(_st(rig)["targets"], ["bet"] + doors, "await_bet with %d exits" % n)
		_tap(rig, "bet")
		assert_eq(_st(rig)["targets"], doors, "dealing with %d exits" % n)
		_until(rig, "player_turn", 20.0)
		assert_eq(_st(rig)["targets"], ["deck", "hand"] + doors, "player_turn with %d exits" % n)
		_tap(rig, "deck")
		assert_eq(_st(rig)["targets"], doors, "a twisted card in flight: only the doors (%d exits)" % n)
		_until(rig, "others", 20.0)
		assert_eq(_st(rig)["targets"], doors, "others with %d exits" % n)
		_until(rig, "settling", 30.0)
		assert_eq(_st(rig)["targets"], doors, "settling with %d exits" % n)
		var s := _st(rig)
		assert_eq((s["exits"] as Array).size(), n)
		assert_true(bool(s["hints"]["exit"]))
		_tap(rig, doors[doors.size() - 1])
		assert_eq(_st(rig)["targets"], [], "nothing while leaving (%d exits)" % n)
		assert_false(_tap(rig, doors[0]), "a door refused while leaving")


func test_the_bare_exit_is_the_default_door_and_a_door_of_another_room_is_refused() -> void:
	var rig := _rig_x(2)
	_sit(rig)
	assert_false(_tap(rig, "exit:somewhere.else"), "not a door of this room")
	assert_false(_tap(rig, "exit:"), "no route")
	assert_eq(_phase(rig), "await_bet")
	assert_true(_tap(rig, "exit"), "the alias")
	var a: BlackjackActivity = rig["a"]
	assert_eq(a.leave_route, "r.art", "the default exit's route")
	assert_eq(_st(rig)["leave_route"], "r.art")
	assert_true(bool(_st(rig)["exits"][0]["chosen"]))
	assert_false(bool(_st(rig)["exits"][1]["chosen"]))
	_adv(rig, 4.0 * BEAT)
	assert_true(a.is_done())
	assert_eq(a.done_route(), "r.art")
	# the other door
	rig = _rig_x(2)
	_sit(rig)
	assert_true(_tap(rig, "exit:r.dorm"))
	a = rig["a"]
	assert_eq(a.leave_route, "r.dorm")
	_adv(rig, 4.0 * BEAT)
	assert_eq(a.done_reason(), "left")
	assert_eq(a.done_route(), "r.dorm")
	# no exits: the plain door gets up with no route
	rig = _rig_x(0)
	_sit(rig)
	assert_false(_tap(rig, "exit:r.art"), "a room without exits has no such door")
	assert_true(_tap(rig, "exit"))
	_adv(rig, 4.0 * BEAT)
	assert_eq((rig["a"] as BlackjackActivity).done_route(), "")


func test_every_door_keeps_the_same_stake_rules() -> void:
	for door in ["exit", "exit:r.art", "exit:r.dorm", "exit:r.yard", "exit:r.lab"]:
		# a live hand: forfeited (decision B4)
		var rig := _rig_x(4, _deal([10, 9], [10, 7]))
		_sit(rig)
		_tap(rig, "bet")
		_until(rig, "player_turn", 20.0)
		assert_true(_tap(rig, door), door)
		assert_eq(_bal(rig), 1500, "%s forfeits a live stake" % door)
		assert_eq(_held(rig), 0)
		_adv(rig, 5.0)
		assert_eq(_bal(rig), 1500, door)
		# between hands: the money is kept
		rig = _rig_x(4, _deal([10, 9], [10, 7]))
		_sit(rig)
		_play(rig, "stick")
		assert_eq(_bal(rig), 2500)
		assert_true(_tap(rig, door))
		_adv(rig, 5.0)
		assert_eq(_bal(rig), 2500, "%s keeps the payout" % door)
		assert_eq(_held(rig), 0)
		# a fall after choosing a door changes nothing: still leaving, no refund of a forfeited stake
		rig = _rig_x(4, _deal([10, 9], [10, 7]))
		_sit(rig)
		_tap(rig, "bet")
		_tap(rig, door)
		(rig["a"] as BlackjackActivity).interrupt("fall", float(rig["t"]))
		_adv(rig, 5.0)
		assert_eq(_bal(rig), 1500, door)
		assert_eq((rig["a"] as BlackjackActivity).done_reason(), "left")
		# an interrupt refunds and carries no route
		rig = _rig_x(4, _deal([10, 9], [10, 7]))
		_sit(rig)
		_tap(rig, "bet")
		(rig["a"] as BlackjackActivity).interrupt("fall", float(rig["t"]))
		_adv(rig, 5.0)
		assert_eq(_bal(rig), 2000, "a fall refunds")
		assert_eq((rig["a"] as BlackjackActivity).done_route(), "", "a fall leaves by no door")


func test_the_snapshot_lists_the_exits_read_only_with_target_urged_and_chosen() -> void:
	var rig := _rig_x(2, _deal([10, 6], [10, 8]), 500)
	var s := _st(rig)
	var ex: Array = s["exits"]
	assert_eq(ex.size(), 2)
	assert_eq(ex.map(func(e: Dictionary) -> String: return str(e["route"])), ["r.art", "r.dorm"])
	assert_eq(str(ex[0]["id"]), "r.exit_art")
	assert_eq(str(ex[1]["scene"]), "dorm")
	assert_eq(str(ex[1]["world"]), "w")
	assert_eq(str(ex[1]["dir"]), "up")
	assert_true(bool(ex[0]["default"]))
	assert_false(bool(ex[1]["default"]))
	assert_false(bool(ex[0]["target"]), "not touchable while sitting")
	assert_true(ex.is_read_only())
	assert_true((ex[0] as Dictionary).is_read_only())
	_sit(rig)
	s = _st(rig)
	assert_true(bool(s["exits"][0]["target"]) and bool(s["exits"][1]["target"]))
	assert_false(bool(s["exits"][0]["urged"]), "not urged with money to bet")
	_play(rig, "stick")
	assert_eq(_phase(rig), "broke")
	s = _st(rig)
	assert_true(bool(s["exits"][0]["urged"]) and bool(s["exits"][1]["urged"]), "both urged when broke")
	assert_true(bool(s["hints"]["exit_urged"]))
	assert_eq(s["targets"], _doors(2), "broke: only the doors")
	assert_true(_tap(rig, "exit:r.dorm"))
	s = _st(rig)
	assert_false(bool(s["exits"][0]["chosen"]))
	assert_true(bool(s["exits"][1]["chosen"]))
	assert_false(bool(s["exits"][1]["target"]))
	assert_false(bool(s["exits"][1]["urged"]))


func test_the_exits_are_normalized_default_first_at_most_four_no_duplicates() -> void:
	var list: Array = [{"route": "b", "dir": "up"}, {"route": "a", "default": true}, {"route": "b"}, {"route": ""}, {"nope": 1}, {"route": "c"}, {"route": "d"}, {"route": "e"}]
	var ex := MinigameActivity.normalize_exits(list)
	assert_eq(ex.map(func(e: Dictionary) -> String: return str(e["route"])), ["a", "b", "c", "d"])
	assert_true(ex.is_read_only())
	assert_eq(MinigameActivity.normalize_exits("junk"), [])
	var two := MinigameActivity.normalize_exits([{"route": "a", "default": true}, {"route": "b", "default": true}])
	assert_eq(two.filter(func(e: Dictionary) -> bool: return bool(e["default"])).size(), 1, "one default")
	assert_true(MinigameActivity.is_exit_target("exit") and MinigameActivity.is_exit_target("exit:x"))
	assert_false(MinigameActivity.is_exit_target("exits") or MinigameActivity.is_exit_target("bet"))


func test_the_snapshot_cache_follows_every_change_of_the_exits() -> void:
	var rig := _rig_x(2, _deal([10, 6], [10, 8]), 500)
	var a: BlackjackActivity = rig["a"]
	var s0 := a.state()
	assert_true(is_same(a.state()["exits"], s0["exits"]), "unchanged: the same shared list")
	_sit(rig)
	var s1 := a.state()
	assert_false(is_same(s1["exits"], s0["exits"]), "the doors became targets: rebuilt")
	assert_true(bool(s1["exits"][0]["target"]))
	_play(rig, "stick")
	var s2 := a.state()
	assert_true(bool(s2["exits"][0]["urged"]), "the broke step rebuilt it")
	_tap(rig, "exit:r.art")
	var s3 := a.state()
	assert_true(bool(s3["exits"][0]["chosen"]), "the tap rebuilt it at once")
	assert_eq(s3["leave_route"], "r.art")
	# a refused door tap changes nothing visible
	var s4 := a.state()
	assert_false(a.tap("exit:r.dorm", float(rig["t"])))
	assert_eq(_stripped(a.state()), _stripped(s4))


func test_leaving_by_a_door_is_deterministic_at_any_frame_rate() -> void:
	var run := func(dt: float) -> Array:
		var rig := _rig_x(2, [], 2000, 5)
		var a: BlackjackActivity = rig["a"]
		var taps := [[5.0 * BEAT, "bet"], [12.0 * BEAT, "exit:r.dorm"]]
		var t := 0.0
		var i := 0
		while t < 30.0 * BEAT:
			var nt := t + dt
			if i < taps.size() and float(taps[i][0]) <= nt:
				nt = float(taps[i][0])
			t = nt
			a.update(t)
			while i < taps.size() and float(taps[i][0]) <= t:
				a.tap(str(taps[i][1]), t)
				i += 1
		return [_stripped(a.state()), a.done_route(), (rig["w"] as RunWallet).balance_pence()]
	var ref: Array = run.call(1.0 / 60.0)
	assert_eq(ref[1], "r.dorm")
	for dt in [1.0 / 30.0, 1.0 / 144.0, 0.047]:
		var other: Array = run.call(dt)
		assert_eq(other[0], ref[0], "the same end at step %f" % dt)
		assert_eq(other[1], ref[1])
		assert_eq(other[2], ref[2])
