class_name BlackjackGame
extends RefCounted
## Simplified blackjack for four seats (two NPCs, the player and the dealer). Pure rules: no wallet,
## no clock, no nodes. Everything it does is appended to `events` so a presentation layer can replay it.
##
## Event kinds (all carry "seat" where it applies):
##   deal    {seat, card:{rank,suit}, face_up, hand, total, twist?}  total counts face-up cards only
##   reveal  {seat:"dealer", card, total}
##   stand   {seat, total}
##   bust    {seat, total}
##   natural {seat, total}
##   result  {seat, result, total, dealer_total}
##   abandon {hand} / clear {hand}

const SEATS: Array[String] = ["npc_a", "player", "npc_b", "dealer"]

var state := "idle"
var hand_number := 0
var events: Array = []

var _deck: BlackjackDeck
var _hands := {}
var _results := {}
var _in := {}


func _init(seed: int = 0, deck: BlackjackDeck = null) -> void:
	_deck = deck if deck != null else BlackjackDeck.new(seed)
	_reset_table()


## Best blackjack total for `cards` (each with "rank"). An ace counts 11 when that does not bust.
static func hand_value(cards: Array) -> Dictionary:
	var total := 0
	var aces := 0
	for c in cards:
		var r := int(c["rank"])
		if r == 1:
			aces += 1
			total += 1
		else:
			total += mini(r, 10)
	var soft := false
	if aces > 0 and total + 10 <= 21:
		total += 10
		soft = true
	return {"total": total, "soft": soft, "bust": total > 21, "natural": cards.size() == 2 and total == 21}


## Money returned for a stake (stake included), integer maths only.
static func payout_pence(stake_pence: int, result: String) -> int:
	match result:
		"blackjack":
			return stake_pence * 5 / 2
		"win":
			return stake_pence * 2
		"push":
			return stake_pence
	return 0


## Deals a new hand. False when a hand is already in progress or finished and not cleared.
func start_hand(player_in: bool = true) -> bool:
	if state != "idle":
		return false
	hand_number += 1
	_reset_table()
	_in = {"npc_a": true, "player": player_in, "npc_b": true, "dealer": true}
	for round_index in range(2):
		for seat in SEATS:
			if _in[seat]:
				_deal(seat, not (seat == "dealer" and round_index == 1), false)
	for seat in SEATS:
		if seat != "dealer" and _in[seat] and value(seat, true)["natural"]:
			events.append({"kind": "natural", "seat": seat, "total": 21})
	if _in["player"] and not value("player")["natural"]:
		state = "player_turn"
	else:
		state = "others"
	return true


## Player draws a card. False (nothing changes) outside the player's turn.
func twist() -> bool:
	if state != "player_turn":
		return false
	_deal("player", true, true)
	var v := value("player")
	if v["bust"]:
		events.append({"kind": "bust", "seat": "player", "total": v["total"]})
		state = "others"
	elif v["total"] == 21:
		events.append({"kind": "stand", "seat": "player", "total": 21})
		state = "others"
	return true


## Player ends their turn. False outside the player's turn.
func stick() -> bool:
	if state != "player_turn":
		return false
	events.append({"kind": "stand", "seat": "player", "total": value("player")["total"]})
	state = "others"
	return true


## Plays npc_a, npc_b and the dealer to completion, then works out results. Only legal in "others".
func play_others() -> bool:
	if state != "others":
		return false
	_play_npc("npc_a")
	_play_npc("npc_b")
	var dealer: Array = _hands["dealer"]
	dealer[1]["face_up"] = true
	events.append({"kind": "reveal", "seat": "dealer", "card": _plain(dealer[1]), "total": value("dealer", true)["total"]})
	if value("dealer")["natural"]:
		events.append({"kind": "natural", "seat": "dealer", "total": 21})
	while value("dealer")["total"] < 17:
		_deal("dealer", true, true)
	var dv := value("dealer")
	if dv["bust"]:
		events.append({"kind": "bust", "seat": "dealer", "total": dv["total"]})
	else:
		events.append({"kind": "stand", "seat": "dealer", "total": dv["total"]})
	for seat in ["npc_a", "player", "npc_b"]:
		if _in[seat]:
			_results[seat] = _judge(seat, dv)
			events.append({"kind": "result", "seat": seat, "result": _results[seat], "total": value(seat)["total"], "dealer_total": dv["total"]})
		else:
			_results[seat] = ""
	state = "done"
	return true


## "bust" | "blackjack" | "push" | "win" | "lose", or "" for a seat not in the hand (or no results yet).
func result(seat: String) -> String:
	if state != "done":
		return ""
	return String(_results.get(seat, ""))


## Done to idle: the cards leave the table. False in any other state.
func clear_hand() -> bool:
	if state != "done":
		return false
	events.append({"kind": "clear", "hand": hand_number})
	_reset_table()
	state = "idle"
	return true


## Throws the hand in from any non-idle state: no results, cards already drawn stay drawn.
func abandon_hand() -> bool:
	if state == "idle":
		return false
	events.append({"kind": "abandon", "hand": hand_number})
	_reset_table()
	state = "idle"
	return true


## Returns the pending events and clears the list.
func drain_events() -> Array:
	var out := events
	events = []
	return out


## The seat's cards, each {"rank","suit","face_up"} (copies).
func cards(seat: String) -> Array:
	var out: Array = []
	for c in _hands.get(seat, []):
		out.append(c.duplicate())
	return out


## hand_value of the seat's cards. With `visible_only` face-down cards are left out.
func value(seat: String, visible_only: bool = false) -> Dictionary:
	var list: Array = []
	for c in _hands.get(seat, []):
		if c["face_up"] or not visible_only:
			list.append(c)
	return hand_value(list)


## The dealer's face-up card, or {} before the deal.
func dealer_up_card() -> Dictionary:
	var d: Array = _hands.get("dealer", [])
	if d.is_empty():
		return {}
	return d[0].duplicate()


func _reset_table() -> void:
	_hands = {}
	_results = {}
	_in = {}
	for seat in SEATS:
		_hands[seat] = []
		_in[seat] = false
		_results[seat] = ""


func _on_table() -> Array:
	var out: Array = []
	for seat in SEATS:
		out.append_array(_hands[seat])
	return out


func _plain(card: Dictionary) -> Dictionary:
	return {"rank": card["rank"], "suit": card["suit"]}


func _deal(seat: String, face_up: bool, hit: bool) -> void:
	var c := _deck.draw(_on_table())
	var card := {"rank": int(c["rank"]), "suit": int(c["suit"]), "face_up": face_up}
	_hands[seat].append(card)
	var e := {"kind": "deal", "seat": seat, "card": _plain(card), "face_up": face_up, "hand": hand_number, "total": value(seat, true)["total"]}
	if hit:
		e["twist"] = true
	events.append(e)


func _dealer_up_value() -> int:
	var r := int(dealer_up_card()["rank"])
	if r == 1:
		return 11
	return mini(r, 10)


func _npc_hits(seat: String) -> bool:
	var v := value(seat)
	var t: int = v["total"]
	if t >= 21:
		return false
	if v["soft"]:
		return t <= 17
	if t < 12:
		return true
	if t <= 16:
		return _dealer_up_value() >= 7
	return false


func _play_npc(seat: String) -> void:
	while _npc_hits(seat):
		_deal(seat, true, true)
	var v := value(seat)
	if v["bust"]:
		events.append({"kind": "bust", "seat": seat, "total": v["total"]})
	else:
		events.append({"kind": "stand", "seat": seat, "total": v["total"]})


func _judge(seat: String, dealer: Dictionary) -> String:
	var v := value(seat)
	if v["bust"]:
		return "bust"
	if v["natural"]:
		return "push" if dealer["natural"] else "blackjack"
	if dealer["natural"]:
		return "lose"
	if dealer["bust"] or v["total"] > dealer["total"]:
		return "win"
	if v["total"] == dealer["total"]:
		return "push"
	return "lose"
