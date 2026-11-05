class_name BlackjackActivity
extends MinigameActivity
## The blackjack director (docs/BLACKJACK_INTEGRATION.md section 6): pure, deterministic logic that binds a BlackjackGame and the run's RunWallet to a song-time timeline and describes,
## as data, everything the view draws. No nodes, no clock, no randomness of its own (the only random stream is the deck's, owner decision B6): any variety in the people's reactions comes
## from the hand number and the seat.
##
## Inputs: `begin(t)`, `tap(target, t)`, `set_wobble(level, t)`, `request_leave(t)`, `interrupt(reason, t)`, `update(t)`; song time only increases. Internally an ordered schedule of future
## steps fires when `update(t)` (or any input) passes their time, and every step takes effect AT ITS OWN TIME, so the snapshot at song time T is the same however often `update` ran.
## A tap takes effect at the tap's time. All durations are beats (config "timing_beats") times `beat_s`.
##
## Money: tag "blackjack". Bet touched: hold(stake). The dealer's settle step (a definite song time in `settling`): settle(payout). Leaving by choice with a live stake: settle(0), the forfeit.
## `interrupt`: release (refund). Never twice: a live-stake flag plus the wallet's own tag rules.
##
## Phases: "" (before begin), sitting, await_bet, dealing, player_turn, others, settling, broke, leaving, falling. Targets: await_bet [bet, exit]; dealing, others, settling, broke [exit];
## player_turn [deck, hand, exit] (just [exit] while a twisted card is in flight); sitting, leaving, falling [].
##
## state() snapshot:
##   { "phase", "phase_t0", "t" (last update time), "hand", "stake_pence", "wobble": {level, t0},
##     "seats": {"npc_a", "player", "npc_b", "dealer": S}, "pile": P, "bet": B, "targets": [ids],
##     "hints": {bet, deck, hand, exit, exit_urged}, "done", "done_reason" }
##   S = { "cards": [ {rank, suit, face_up (as of now), t_deal (leaves the deck), t_land (arrives), t_flip (-1 never), t_clear (-1 not yet)} ], "total" (landed face-up cards),
##         "result" ("" until settled), "mood": {name, t0}, "gaze": {target, t0}, "gesture": {name, t0, dur} }  (the player's gesture uses the player-hand vocabulary)
##   P = { "pence", "from_pence", "t0", "dur", "via" }: the pile (always the wallet's balance, except 0 while leaving). Animate from_pence to pence over t0..t0+dur; `via` names the other end of the
##       movement: "" none, "pockets" (sitting: out of the pockets; leaving: back into them), "bet" (the stake went to / came back from the bet spot), "dealer" (paid by the dealer).
##   B = { "pence" (always the wallet's held stake), "from_pence", "t0", "dur", "via" }: via "" none, "pile" (the stake came from / went back to the pile), "dealer" (swept away by the dealer).
## Cards dealt whose t_deal is still in the future are included (the view hides them until then). A cleared hand's cards stay (with t_clear) until the next hand is dealt.

const TAG := "blackjack"
const SEATS: Array[String] = ["npc_a", "player", "npc_b", "dealer"]
const NPCS: Array[String] = ["npc_a", "npc_b"]
const DEFAULT_TIMING := {
	"sit_pockets": 2.0, "sit_lay": 2.0, "sit_invite": 1.0, "invite_gaze": 1.5, "bet_move": 1.5, "deal_gap": 0.5, "deal_flight": 0.5, "twist_flight": 1.0, "act": 1.0,
	"point_period": 2.0, "react": 1.5, "others_lead": 1.5, "npc_ask": 1.0, "npc_pause": 0.5, "npc_stand": 1.5, "reveal": 1.5, "dealer_gap": 1.0, "end_react": 1.5,
	"settle_delay": 1.0, "settle_move": 2.0, "settle_show": 3.0, "clear": 1.0, "leave": 3.0, "fall": 4.0,
}

var _game: BlackjackGame
var _timing: Dictionary = {}
var _stake := 500
var _phase := ""
var _phase_t0 := 0.0
var _pid := 0  # bumped at every phase change; guarded steps of an older phase are dropped
var _now := 0.0
var _last := 0.0
var _steps: Array = []
var _seq := 0
var _hand := 0
var _live := false  # a stake is held and not yet settled or released
var _busy := false  # a twisted card is in flight
var _seats: Dictionary = {}
var _pile: Dictionary = {}
var _bet: Dictionary = {}
var _wobble: Dictionary = {"level": 0, "t0": 0.0}
## The snapshot is built once and reused until something can have changed it: `_ver` is bumped by every input and every step that fires (all of the activity's state changes inside those),
## `_snap_until` is the next song time at which a card turns over or lands (the only parts of the snapshot that move with time alone), and the wallet's money is compared directly.
var _ver := 0
var _snap: Dictionary = {}
var _snap_ver := -1
var _snap_until := -INF
var _snap_money := Vector2i(-1, -1)


func setup(ctx: Dictionary) -> void:
	_ver += 1
	super.setup(ctx)
	if wallet == null:
		wallet = RunWallet.new()
		wallet.spend(wallet.balance_pence())
	_timing = DEFAULT_TIMING.duplicate()
	var tb: Variant = config.get("timing_beats", {})
	if typeof(tb) == TYPE_DICTIONARY:
		for k in tb:
			_timing[k] = float(tb[k])
	_stake = int(config.get("stake_pence", 500))
	var deck: Variant = ctx.get("deck", null)
	_game = BlackjackGame.new(rng_seed, deck if deck is BlackjackDeck else null)
	for seat in SEATS:
		_seats[seat] = {"cards": [], "result": "", "mood": {"name": "neutral", "t0": 0.0}, "gaze": {"target": "own_cards" if seat == "player" else "player", "t0": 0.0}, "gesture": {"name": "none" if seat == "player" else "rest", "t0": 0.0, "dur": 0.0}}
	_pile = {"from": wallet.balance_pence(), "t0": 0.0, "dur": 0.0, "via": ""}
	_bet = {"from": 0, "t0": 0.0, "dur": 0.0, "via": ""}


func begin(t: float) -> void:
	if began:
		return
	_ver += 1
	super.begin(t)
	_now = t
	_last = t
	_enter_phase("sitting", t)
	var sp := _b("sit_pockets")
	var sl := _b("sit_lay")
	_gesture("player", "pockets", t, sp)
	_gesture("player", "lay_money", t + sp, sl)
	_pile = {"from": 0, "t0": t + sp, "dur": sl, "via": "pockets"}
	_gaze_all(t, "player")
	_mood("npc_a", "happy" if _par("npc_a") == 0 else "neutral", t)
	_mood("npc_b", "happy" if _par("npc_b") == 0 else "neutral", t)
	_gesture(NPCS[0], "invite", t + _b("sit_invite"), _b("act"))
	_at(t + sp + sl, "ready", {"pid": _pid})


func update(t: float) -> void:
	_advance(t)


func targets() -> Array:
	if _done:
		return []
	match _phase:
		"await_bet":
			return ["bet", "exit"]
		"player_turn":
			return ["exit"] if _busy else ["deck", "hand", "exit"]
		"dealing", "others", "settling", "broke":
			return ["exit"]
	return []


func tap(target: String, t: float) -> bool:
	if not began or _done:
		return false
	_advance(t)
	_ver += 1
	if not (target in targets()):
		return false
	match target:
		"exit":
			_start_leave(_now)
			return true
		"bet":
			return _do_bet(_now)
		"deck":
			_do_twist(_now)
			return true
		"hand":
			_do_stick(_now)
			return true
	return false


func set_wobble(level: int, t: float) -> void:
	_advance(t)
	if level == int(_wobble["level"]):
		return
	_ver += 1
	super.set_wobble(level, t)
	_wobble = {"level": level, "t0": _now}


func request_leave(t: float) -> void:
	_ver += 1
	if not began:
		_finish("left")
		return
	_advance(t)
	if _done or _phase == "leaving" or _phase == "falling":
		return
	_start_leave(_now)


func interrupt(reason: String, t: float) -> void:
	_ver += 1
	if not began:
		_finish(reason)
		return
	_advance(t)
	if _done or _phase == "leaving" or _phase == "falling":
		return
	if reason == "fall":
		_start_fall(_now)
	else:
		_start_stop(_now, reason)


func make_view() -> Control:
	return BlackjackView.new()


## The snapshot (schema above). Every call returns a fresh top-level dictionary; the nested parts are shared with other calls until something changes and are read-only.
func state() -> Dictionary:
	var money := Vector2i(wallet.balance_pence(), wallet.held_pence())
	if _snap_ver != _ver or _now >= _snap_until or money != _snap_money:
		_snap = _build_state()
		_snap_ver = _ver
		_snap_money = money
	var out := _snap.duplicate()
	out["t"] = _last
	return out


func _build_state() -> Dictionary:
	_snap_until = INF
	var seats := {}
	var override := int(_wobble["level"]) == 1 and _phase != "falling" and _phase != ""
	for seat in SEATS:
		var s: Dictionary = _seats[seat]
		var cards: Array = []
		var visible: Array = []
		for c in s["cards"]:
			var flip := float(c["t_flip"])
			var up := bool(c["up"]) or (flip >= 0.0 and _now >= flip)
			cards.append(_frozen({"rank": c["rank"], "suit": c["suit"], "face_up": up, "t_deal": c["t_deal"], "t_land": c["t_land"], "t_flip": flip, "t_clear": c["t_clear"]}))
			if up and _now >= float(c["t_land"]):
				visible.append(c)
			if flip > _now:
				_snap_until = minf(_snap_until, flip)
			if float(c["t_land"]) > _now:
				_snap_until = minf(_snap_until, float(c["t_land"]))
		var mood: Dictionary = (s["mood"] as Dictionary).duplicate()
		var gaze: Dictionary = (s["gaze"] as Dictionary).duplicate()
		if override and seat == "dealer":
			mood = {"name": "concerned", "t0": _wobble["t0"]}
			gaze = {"target": "player", "t0": _wobble["t0"]}
		seats[seat] = _frozen({"cards": _frozen(cards), "total": int(BlackjackGame.hand_value(visible)["total"]), "result": s["result"], "mood": _frozen(mood), "gaze": _frozen(gaze),
			"gesture": _frozen((s["gesture"] as Dictionary).duplicate())})
	var tg := targets()
	var balance: int = wallet.balance_pence()
	return {
		"phase": _phase, "phase_t0": _phase_t0, "t": _last, "hand": _hand, "stake_pence": _stake,
		"wobble": _frozen(_wobble.duplicate()), "seats": _frozen(seats),
		"pile": _frozen({"pence": 0 if _phase == "leaving" else balance, "from_pence": _pile["from"], "t0": _pile["t0"], "dur": _pile["dur"], "via": _pile["via"]}),
		"bet": _frozen({"pence": wallet.held_pence(), "from_pence": _bet["from"], "t0": _bet["t0"], "dur": _bet["dur"], "via": _bet["via"]}),
		"targets": _frozen(tg),
		"hints": _frozen({"bet": "bet" in tg, "deck": "deck" in tg, "hand": "hand" in tg, "exit": "exit" in tg, "exit_urged": _phase == "broke"}),
		"done": _done, "done_reason": _reason,
	}


## Makes a part of the snapshot read-only (it is shared between snapshots) and returns it.
static func _frozen(v: Variant) -> Variant:
	if v is Dictionary:
		(v as Dictionary).make_read_only()
	elif v is Array:
		(v as Array).make_read_only()
	return v


# time and schedule

func _b(key: String) -> float:
	return float(_timing[key]) * beat_s


func _par(seat: String, salt := 0) -> int:
	return (_hand + SEATS.find(seat) + salt) % 2


func _at(t: float, op: String, args: Dictionary = {}) -> void:
	var s := args.duplicate()
	s["t"] = t
	s["op"] = op
	s["seq"] = _seq
	_seq += 1
	var i := _steps.size()
	while i > 0 and float(_steps[i - 1]["t"]) > t:
		i -= 1
	_steps.insert(i, s)


func _advance(t: float) -> void:
	while not _steps.is_empty() and float(_steps[0]["t"]) <= t:
		var s: Dictionary = _steps.pop_front()
		_now = maxf(_now, float(s["t"]))
		_ver += 1
		if int(s.get("pid", -1)) != -1 and int(s["pid"]) != _pid:
			continue
		_run(s)
	_now = maxf(_now, t)
	_last = maxf(_last, t)


func _run(s: Dictionary) -> void:
	var t := float(s["t"])
	match String(s["op"]):
		"mood":
			_set_mood(String(s["seat"]), String(s["name"]), t)
		"gaze":
			_set_gaze(String(s["seat"]), String(s["target"]), t)
		"gesture":
			_set_gesture(String(s["seat"]), String(s["name"]), t, float(s["dur"]))
		"ready":
			_enter_ready(t)
		"dealt":
			_dealt(t)
		"point":
			_point(t, int(s["k"]))
		"twist_land":
			_twist_land(t)
		"to_settling":
			_to_settling(t)
		"settle":
			_settle(t)
		"clear":
			_clear_table(t)
		"finish":
			_finish(String(s["reason"]))


func _enter_phase(name: String, t: float) -> void:
	_phase = name
	_phase_t0 = t
	_pid += 1


func _set_mood(seat: String, name: String, t: float) -> void:
	var m: Dictionary = _seats[seat]["mood"]
	if m["name"] != name:
		_seats[seat]["mood"] = {"name": name, "t0": t}


func _set_gaze(seat: String, target: String, t: float) -> void:
	var g: Dictionary = _seats[seat]["gaze"]
	if g["target"] != target:
		_seats[seat]["gaze"] = {"target": target, "t0": t}


func _set_gesture(seat: String, name: String, t: float, dur: float) -> void:
	_seats[seat]["gesture"] = {"name": name, "t0": t, "dur": dur}


## Mood / gaze / gesture at time `t`: now when `t` is not in the future, else scheduled.
func _mood(seat: String, name: String, t: float) -> void:
	if t <= _now:
		_set_mood(seat, name, t)
	else:
		_at(t, "mood", {"seat": seat, "name": name})


func _gaze(seat: String, target: String, t: float) -> void:
	if t <= _now:
		_set_gaze(seat, target, t)
	else:
		_at(t, "gaze", {"seat": seat, "target": target})


func _gesture(seat: String, name: String, t: float, dur: float) -> void:
	if t <= _now:
		_set_gesture(seat, name, t, dur)
	else:
		_at(t, "gesture", {"seat": seat, "name": name, "dur": dur})


func _gaze_all(t: float, target: String, include_player := false) -> void:
	for seat in SEATS:
		if seat != "player" or include_player:
			_gaze(seat, target, t)


# phases

func _enter_ready(t: float) -> void:
	for seat in SEATS:
		if seat != "player":
			_mood(seat, "neutral", t)
	if wallet.can_afford(_stake):
		_enter_phase("await_bet", t)
		_gesture("dealer", "invite", t, _b("act") * 2.0)
		_gaze("dealer", "bet", t)
		_gaze("dealer", "player", t + _b("invite_gaze"))
		_gaze("npc_a", "dealer", t)
		_gaze("npc_b", "dealer", t)
		_gesture("player", "none", t, 0.0)
	else:
		_enter_phase("broke", t)
		_gesture("player", "empty_pockets", t, _b("act") * 2.0)
		_gesture("dealer", "shrug", t, _b("act") * 2.0)
		_mood("dealer", "concerned", t)
		_gaze("dealer", "player", t)
		_gaze("npc_a", "own_cards", t)
		_gaze("npc_b", "own_cards", t)
		_mood("npc_a", "neutral", t)
		_mood("npc_b", "neutral", t)


func _do_bet(t: float) -> bool:
	if not wallet.hold(TAG, _stake):
		return false
	_live = true
	var bm := _b("bet_move")
	_enter_phase("dealing", t)
	_pile = {"from": wallet.balance_pence() + _stake, "t0": t, "dur": bm, "via": "bet"}
	_bet = {"from": 0, "t0": t, "dur": bm, "via": "pile"}
	_gesture("player", "push_bet", t, bm)
	for seat in SEATS:
		_seats[seat]["cards"] = []
		_seats[seat]["result"] = ""
	_game.start_hand(true)
	_hand = _game.hand_number
	var first := t + bm
	var gap := _b("deal_gap")
	var flight := _b("deal_flight")
	var counts := {}
	var last_land := first
	var i := 0
	_gaze("dealer", "deck", t)
	_gaze("npc_a", "dealer", t)
	_gaze("npc_b", "dealer", t)
	for e in _game.drain_events():
		if e["kind"] != "deal":
			continue
		var seat := String(e["seat"])
		var td := first + float(i) * gap
		var tl := td + flight
		i += 1
		_add_card(seat, e["card"], bool(e["face_up"]), td, tl)
		_gesture("dealer", "deal", td, _b("act"))
		last_land = tl
		counts[seat] = int(counts.get(seat, 0)) + 1
		if int(counts[seat]) == 2 and seat != "dealer":
			var cards: Array = _seats[seat]["cards"]
			if BlackjackGame.hand_value(cards)["natural"]:
				_natural_reaction(seat, tl)
	_at(last_land, "dealt", {"pid": _pid})
	return true


func _natural_reaction(seat: String, t: float) -> void:
	if seat == "player":
		for other in ["npc_a", "npc_b", "dealer"]:
			_mood(other, "surprised", t)
			_mood(other, "happy", t + _b("react"))
		_mood("player", "happy", t)
	else:
		_mood(seat, "laugh" if _par(seat) == 0 else "happy", t)


func _add_card(seat: String, card: Dictionary, up: bool, td: float, tl: float) -> Dictionary:
	var c := {"rank": int(card["rank"]), "suit": int(card["suit"]), "up": up, "t_deal": td, "t_land": tl, "t_flip": -1.0, "t_clear": -1.0}
	_seats[seat]["cards"].append(c)
	return c


func _dealt(t: float) -> void:
	if _game.state == "player_turn":
		_enter_phase("player_turn", t)
		_gaze("dealer", "player", t)
		_gaze("npc_a", "player" if _par("npc_a") == 0 else "own_cards", t)
		_gaze("npc_b", "player" if _par("npc_b") == 0 else "own_cards", t)
		_point(t, 0)
	else:
		_begin_others(t)


func _point(t: float, k: int) -> void:
	if not _busy:
		_set_gesture("dealer", "point_deck" if k % 2 == 0 else "point_hand", t, _b("point_period"))
	_at(t + _b("point_period"), "point", {"pid": _pid, "k": k + 1})


func _do_twist(t: float) -> void:
	_game.twist()
	_game.drain_events()
	var seat_cards: Array = _game.cards("player")
	var c: Dictionary = seat_cards[seat_cards.size() - 1]
	var tf := _b("twist_flight")
	_add_card("player", c, true, t, t + tf)
	_busy = true
	_gesture("player", "reach_deck", t, tf)
	_gesture("dealer", "deal", t, _b("act"))
	_at(t + tf, "twist_land", {"pid": _pid})


func _twist_land(t: float) -> void:
	_busy = false
	if _game.state == "player_turn":
		return
	if _game.value("player")["bust"]:
		_gesture("player", "drop_cards", t, _b("act"))
		for n in NPCS:
			_mood(n, "wince" if _par(n) == 0 else "smug", t)
		_mood("dealer", "sad" if _par("dealer") == 0 else "neutral", t)
	_begin_others(t)


func _do_stick(t: float) -> void:
	_game.stick()
	_game.drain_events()
	_gesture("player", "cover_cards", t, _b("act"))
	_begin_others(t)


## Plays the NPCs and the dealer in the game once and lays the events out in time from `t`.
func _begin_others(t: float) -> void:
	_enter_phase("others", t)
	_game.play_others()
	var events := _game.drain_events()
	var c := t + _b("others_lead")
	var flight := _b("deal_flight")
	_gaze("dealer", "deck", t)
	for e in events:
		var seat := String(e["seat"])
		match String(e["kind"]):
			"deal":
				if seat == "dealer":
					_add_card(seat, e["card"], true, c, c + flight)
					_gesture("dealer", "deal", c, _b("act"))
					c += _b("dealer_gap")
				else:
					var td := c + _b("npc_ask")
					_gesture(seat, "tap_table", c, _b("act"))
					_gaze("dealer", seat, c)
					_gesture("dealer", "deal", td, _b("act"))
					_add_card(seat, e["card"], true, td, td + flight)
					c = td + flight + _b("npc_pause")
			"stand":
				if seat == "dealer":
					c += _b("npc_pause")
				elif seat != "player":
					_gesture(seat, "wave_off", c, _b("act"))
					c += _b("npc_stand")
			"bust":
				if seat == "dealer":
					_mood("dealer", "annoyed", c)
					for n in NPCS:
						_mood(n, "happy", c)
					c += _b("end_react")
				elif seat != "player":
					_mood(seat, "annoyed" if _par(seat) == 0 else "sad", c)
					_mood("npc_b" if seat == "npc_a" else "npc_a", "smug", c)
					c += _b("end_react")
			"reveal":
				_gaze("dealer", "own_cards", c)
				for card in _seats["dealer"]["cards"]:
					if not bool(card["up"]) and float(card["t_flip"]) < 0.0:
						card["t_flip"] = c
				c += _b("reveal")
			"natural":
				if seat == "dealer":
					_mood("dealer", "laugh", c)
	_at(c, "to_settling", {"pid": _pid})


func _to_settling(t: float) -> void:
	_enter_phase("settling", t)
	_at(t + _b("settle_delay"), "settle", {"pid": _pid})


func _settle(t: float) -> void:
	var res := _game.result("player")
	var payout := BlackjackGame.payout_pence(_stake, res)
	var before: int = wallet.balance_pence()
	if _live:
		wallet.settle(TAG, payout)
		_live = false
	for seat in ["npc_a", "player", "npc_b"]:
		_seats[seat]["result"] = _game.result(seat)
	var mv := _b("settle_move")
	_gaze_all(t, "player")
	_gaze("player", "own_cards", t)
	match res:
		"blackjack", "win":
			_gesture("dealer", "pay", t, mv)
			_pile = {"from": before, "t0": t, "dur": mv, "via": "dealer"}
			_bet = {"from": _stake, "t0": t, "dur": mv, "via": "pile"}
		"push":
			_gesture("dealer", "rest", t, 0.0)
			_pile = {"from": before, "t0": t, "dur": mv, "via": "bet"}
			_bet = {"from": _stake, "t0": t, "dur": mv, "via": "pile"}
		_:
			_gesture("dealer", "sweep", t, mv)
			_pile = {"from": before, "t0": t, "dur": 0.0, "via": ""}
			_bet = {"from": _stake, "t0": t, "dur": mv, "via": "dealer"}
	_settle_moods(res, t)
	_at(t + _b("settle_show"), "clear", {"pid": _pid})


func _settle_moods(res: String, t: float) -> void:
	var react := _b("react")
	if res == "blackjack":
		for n in NPCS:
			_mood(n, "surprised", t)
			if _par(n) == 0:
				_mood(n, "laugh", t + react)
			else:
				_gesture(n, "clap", t + react, _b("act") * 2.0)
		_mood("dealer", "surprised", t)
		return
	if res == "win":
		_mood("dealer", "annoyed" if _par("dealer") == 0 else "neutral", t)
	elif res == "push":
		_mood("dealer", "neutral", t)
	else:
		_mood("dealer", "smug" if _par("dealer") == 0 else "neutral", t)
	for n in NPCS:
		var own := _game.result(n)
		var mood := "neutral"
		if own == "lose" or own == "bust":
			mood = "sad" if _par(n) == 0 else "annoyed"
		elif res == "win":
			mood = "happy" if _par(n) == 0 else "annoyed"
		elif res == "push":
			mood = "neutral" if _par(n) == 0 else "thinking"
		else:
			mood = "smug" if own == "win" or own == "blackjack" else "wince"
		_mood(n, mood, t)


func _clear_table(t: float) -> void:
	for seat in SEATS:
		for c in _seats[seat]["cards"]:
			if float(c["t_clear"]) < 0.0:
				c["t_clear"] = t
	_game.clear_hand()
	_at(t + _b("clear"), "ready", {"pid": _pid})


# leaving and interrupts

## Stops the hand where it is: pending steps dropped, a hand in progress abandoned and its cards cleared.
func _stop_hand(t: float) -> void:
	_steps.clear()
	_busy = false
	if _game.state != "idle":
		_game.abandon_hand()
		_game.drain_events()
	for seat in SEATS:
		var keep: Array = []
		for c in _seats[seat]["cards"]:
			if float(c["t_deal"]) > t:
				continue
			if float(c["t_clear"]) < 0.0:
				c["t_clear"] = t
			keep.append(c)
		_seats[seat]["cards"] = keep


func _start_leave(t: float) -> void:
	var forfeited := _live
	if _live:
		wallet.settle(TAG, 0)
		_live = false
		_bet = {"from": _stake, "t0": t, "dur": _b("bet_move"), "via": "dealer"}
	_stop_hand(t)
	_enter_phase("leaving", t)
	var dur := _b("leave")
	_gesture("dealer", "sweep" if forfeited else "rest", t, _b("act"))
	_gesture("player", "gather_money", t, dur)
	_pile = {"from": wallet.balance_pence(), "t0": t, "dur": dur, "via": "pockets"}
	_gaze_all(t, "player")
	_at(t + dur, "finish", {"reason": "left"})


func _start_fall(t: float) -> void:
	if _live:
		var held: int = wallet.held_pence()
		var before: int = wallet.balance_pence()
		wallet.release(TAG)
		_live = false
		_pile = {"from": before, "t0": t, "dur": _b("bet_move"), "via": "bet"}
		_bet = {"from": held, "t0": t, "dur": _b("bet_move"), "via": "pile"}
	_stop_hand(t)
	_enter_phase("falling", t)
	_gesture("player", "drop_cards", t, _b("act"))
	_gesture("dealer", "rest", t, 0.0)
	_gaze_all(t, "player")
	for seat in SEATS:
		if seat == "player":
			continue
		_mood(seat, "surprised", t)
		_mood(seat, "laugh" if _par(seat) == 0 else "concerned", t + _b("react"))
	_at(t + _b("fall"), "finish", {"reason": "fall"})


## run_over / host: refund, abandon, done at once.
func _start_stop(t: float, reason: String) -> void:
	if _live:
		var held: int = wallet.held_pence()
		var before: int = wallet.balance_pence()
		wallet.release(TAG)
		_live = false
		_pile = {"from": before, "t0": t, "dur": 0.0, "via": "bet"}
		_bet = {"from": held, "t0": t, "dur": 0.0, "via": "pile"}
	_stop_hand(t)
	_enter_phase("leaving", t)
	_finish(reason)
