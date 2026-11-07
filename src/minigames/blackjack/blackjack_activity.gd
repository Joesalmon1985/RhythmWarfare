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
## player_turn [deck, hand, exit] (just [exit] while a twisted card is in flight); sitting, leaving, falling []. Where the room gave exits, "exit" stands for one "exit:<route>" per exit
## (MinigameActivity, `exit_targets`); the bare "exit" is then still accepted as the default exit. Every door leaves the same way (the stake rules are the same whichever door).
##
## state() snapshot:
##   { "phase", "phase_t0", "t" (last update time), "hand", "stake_pence", "wobble": {level, t0},
##     "seats": {"npc_a", "player", "npc_b", "dealer": S}, "pile": P, "bet": B, "targets": [ids],
##     "hints": {bet, deck, hand, exit, exit_urged}, "exits": [X], "leave_route", "done", "done_reason" }
##   X = { "route", "id" (the exit hotspot), "scene", "world" (the destination's), "dir", "default", "tint", "light", "target" (touchable now), "urged" (leaving is the thing to do: broke),
##         "chosen" (the door the player is leaving by) }, one per exit of the room in the room's order (default first); empty when the room gave none.
##   S = { "cards": [ {rank, suit, face_up (as of now), t_deal (leaves the deck), t_land (arrives), t_flip (-1 never), t_clear (-1 not yet)} ], "total" (landed face-up cards),
##         "result" ("" until settled), "mood": {name, t0}, "gaze": {target, t0}, "gesture": {name, t0, dur} }  (the player's gesture uses the player-hand vocabulary)
##   P = { "pence", "from_pence", "t0", "dur", "via" }: the pile (always the wallet's balance, except 0 while leaving). Animate from_pence to pence over t0..t0+dur; `via` names the other end of the
##       movement: "" none, "pockets" (sitting: out of the pockets; leaving: back into them), "bet" (the stake went to / came back from the bet spot), "dealer" (paid by the dealer).
##   B = { "pence" (always the wallet's held stake), "from_pence", "t0", "dur", "via" }: via "" none, "pile" (the stake came from / went back to the pile), "dealer" (swept away by the dealer).
## Cards dealt whose t_deal is still in the future are included (the view hides them until then). A cleared hand's cards stay (with t_clear) until the next hand is dealt.
##   "people": {seat: {state, t0}} for dealer, npc_a, npc_b: the people state each crowd actor plays (people_state_of), "npc_chips": {npc_a, npc_b}, "bet_steps" (the stake in steps).
##
## STAGING (CONTRACTS.md 10, ruling 38; package A8b): played in the day room, nothing drawn by the activity. `things()` are the cards (sheet bj_cards, one thing a dealt card,
## sliding from the deck to its seat's spot on the felt in song time, face or back, sliding back at the clear), the deck, a chip stack per player whose frame is the stack's
## height (the player's own stack is the wallet's balance, chip_frame) and the bet pile (the held stake); the three other people are the day room's crowd actors (ACTORS),
## directed through `world.people` whenever their people state changes (at the exact song time it changed); feedback marks through `world.feedback` (a tick on a winning
## hand's cards, a cross on a bust, a glow on the player's stack at a payout). The controls (`controls()`): bet (each press in the betting window adds a step of the stake),
## twist (the deck), stick (the hand), get up (exit), pictograms in the pad slots. Mode REPLACE (content/minigames/blackjack.json): the rhythm is suspended while seated.

const TAG := "blackjack"
const SEATS: Array[String] = ["npc_a", "player", "npc_b", "dealer"]
const NPCS: Array[String] = ["npc_a", "npc_b"]
## The crowd actors of the room who sit at the table (content/story/mental_hospital.json; the map's homes put them at the table).
const ACTORS := {"dealer": "cards_dealer", "npc_a": "cards_a", "npc_b": "cards_b"}
## The people states the activity asks for (CONTRACTS.md 10; StoryCrowd resolves each to the sheet's row or a named fallback).
const PEOPLE_STATES := ["idle", "deal", "look", "happy", "frown", "clap"]
const CARDS := "res://assets/minigames/blackjack/bj_cards.png"  # 13 x 5: suit * 13 + rank - 1; 52 the back, 53 a blank (PLACEHOLDER art, tools/minigames/make_card_things.py)
const CHIPS := "res://assets/minigames/blackjack/bj_chips.png"  # 16 x 8: (colour * 2 + change) * 16 + chips (PLACEHOLDER art)
const BACK := 52
const MAX_CHIPS := 15
const CHIP_PENCE := 500  # one chip is five pounds; the pence under that show as a coin beside the stack
const CHIP_COLOUR := {"player": 0, "npc_a": 1, "npc_b": 2, "bet": 3}
const BET_STEPS := 4  # the most stake steps on one hand (config "bet_steps")
## Where things stand on the table (metres, the day room's map; config "staging" overrides any key). The map's `cards_table` occluder stands at z 3.3 with the felt at 0.82 to
## 0.97 m: the player's own things stand just nearer than it (near_z, on the near edge of the felt), the others' just behind it (far_z, the far edge), so the table hides
## nothing that is meant to be seen and the players stand behind their cards. cards_x: where a seat's first card goes (the rest fan to the right by `fan`).
const STAGING := {
	"sector": "dayroom", "near_z": 3.45, "far_z": 3.1, "near_y": 0.84, "far_y": 0.99, "card": [0.21, 0.3], "fan": 0.12, "chip": [0.14, 0.35],
	"cards_x": {"npc_a": 1.5, "dealer": 2.12, "npc_b": 3.02, "player": 2.32},
	"deck": [2.78, 3.1, 1.0], "stack_x": {"player": 1.72, "npc_a": 1.32, "npc_b": 3.58}, "bet_x": 2.02,
}
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
var world: Object = null  # the room (WorldThings: ctx["world"]); null in a pure test
var feedback_log: Array = []  # [{thing, kind, t}] every feedback mark asked for (also when there is no world)
var people_log: Array = []  # [{id, seat, state, t}] every people direction given (also when there is no world)
var _step := 500  # one stake step (config stake_pence)
var _max_steps := BET_STEPS
var _first_deal := INF  # song time the hand's first card leaves the deck: the betting window closes then
var _npc_chips := {"npc_a": 7, "npc_b": 9}
var _people: Dictionary = {}  # seat -> {state, t0}: what was last asked of each person
var _stage: Dictionary = {}


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
	_step = int(config.get("stake_pence", 500))
	_stake = _step
	_max_steps = maxi(int(config.get("bet_steps", BET_STEPS)), 1)
	world = ctx.get("world", null)
	_stage = STAGING.duplicate(true)
	var stg: Variant = config.get("staging", {})
	if typeof(stg) == TYPE_DICTIONARY:
		_stage.merge(stg, true)
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
	# the welcome: all three pleased to have you, the dealer's open palm toward your seat, the two players beckoning you in one after the other
	_gaze_all(t, "player")
	for seat in SEATS:
		if seat != "player":
			_mood(seat, "happy", t)
	_gesture("dealer", "invite", t, _b("act") * 2.0)
	_gesture(NPCS[0], "invite", t + _b("sit_invite"), _b("act"))
	_gesture(NPCS[1], "invite", t + _b("sit_invite") + _b("act"), _b("act"))
	_at(t + sp + sl, "ready", {"pid": _pid})


func update(t: float) -> void:
	_advance(t)
	_sync_people()


func targets() -> Array:
	if _done:
		return []
	var ex := exit_targets()
	match _phase:
		"await_bet":
			return ["bet"] + ex
		"player_turn":
			return ex.duplicate() if _busy else ["deck", "hand"] + ex
		"dealing":
			return (["bet"] + ex) if _can_raise() else ex.duplicate()
		"others", "settling", "broke":
			return ex.duplicate()
	return []


func tap(target: String, t: float) -> bool:
	if not began or _done:
		return false
	_advance(t)
	_ver += 1
	var id := exit_alias(target)  # the bare "exit" is the default door
	if not (id in targets()):
		return false
	if is_exit_target(id):
		leave_route = exit_route(id)
		_start_leave(_now)
		_sync_people()
		return true
	var ok := false
	match id:
		"bet":
			ok = _raise_bet(_now) if _phase == "dealing" else _do_bet(_now)
		"deck":
			_do_twist(_now)
			ok = true
		"hand":
			_do_stick(_now)
			ok = true
	_sync_people()
	return ok


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


## No canvas view (ruling 38): the room draws the table's things and people, the host's controls layer the strip, the host's feedback layer the marks.
func make_view() -> Control:
	return null


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
	for seat: String in ACTORS:  # (a gesture running out changes a person's people state with time alone)
		var g: Dictionary = _seats[seat]["gesture"]
		var g1 := float(g["t0"]) + float(g["dur"])
		if float(g["dur"]) > 0.0 and g1 > _now:
			_snap_until = minf(_snap_until, g1)
	var tg := targets()
	var balance: int = wallet.balance_pence()
	var any_exit := false
	for id: String in tg:
		any_exit = any_exit or is_exit_target(id)
	var doors: Array = []
	for e: Dictionary in exits:
		var x := e.duplicate()
		x["target"] = ("exit:" + str(e["route"])) in tg
		x["urged"] = bool(x["target"]) and _phase == "broke"
		x["chosen"] = _phase == "leaving" and leave_route == str(e["route"])
		doors.append(_frozen(x))
	return {
		"phase": _phase, "phase_t0": _phase_t0, "t": _last, "hand": _hand, "stake_pence": _stake,
		"wobble": _frozen(_wobble.duplicate()), "seats": _frozen(seats),
		"pile": _frozen({"pence": 0 if _phase == "leaving" else balance, "from_pence": _pile["from"], "t0": _pile["t0"], "dur": _pile["dur"], "via": _pile["via"]}),
		"bet": _frozen({"pence": wallet.held_pence(), "from_pence": _bet["from"], "t0": _bet["t0"], "dur": _bet["dur"], "via": _bet["via"]}),
		"targets": _frozen(tg),
		"hints": _frozen({"bet": "bet" in tg, "deck": "deck" in tg, "hand": "hand" in tg, "exit": any_exit, "exit_urged": _phase == "broke"}),
		"exits": _frozen(doors), "leave_route": leave_route,
		"done": _done, "done_reason": _reason,
		"people": _frozen(_people_now()), "npc_chips": _frozen(_npc_chips.duplicate()), "bet_steps": _stake / maxi(_step, 1),
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
	var first := _hand == 0  # the first bet of the visit: the table is still welcoming you
	for seat in SEATS:
		if seat != "player":
			_mood(seat, "happy" if first else "neutral", t)
	if wallet.can_afford(_step):
		_enter_phase("await_bet", t)
		_gesture("dealer", "invite", t, _b("act") * 2.0)
		_gaze("dealer", "bet", t)
		_gaze("dealer", "player", t + _b("invite_gaze"))
		_gaze("npc_a", "player" if first else "dealer", t)
		_gaze("npc_b", "player" if first else "dealer", t)
		if first:  # the welcome settles after a few beats of waiting (dropped once the bet is down: their faces then follow the hand)
			for seat in SEATS:
				if seat != "player":
					_at(t + _b("act") * 4.0, "mood", {"seat": seat, "name": "neutral", "pid": _pid})
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
	_stake = _step
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
	_first_deal = first
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


## Another press of bet in the betting window (before the first card leaves the deck): one more step of the stake, when it can be afforded and the hand is not at its most.
func _can_raise() -> bool:
	return _phase == "dealing" and _live and _now < _first_deal and _stake + _step <= _step * _max_steps and wallet.can_afford(_step)


func _raise_bet(t: float) -> bool:
	if not _can_raise():
		return false
	var old := _stake
	if not wallet.release(TAG):
		return false
	if not wallet.hold(TAG, old + _step):
		wallet.hold(TAG, old)
		return false
	_stake = old + _step
	var bm := _b("bet_move")
	_pile = {"from": wallet.balance_pence() + _step, "t0": t, "dur": bm, "via": "bet"}
	_bet = {"from": old, "t0": t, "dur": bm, "via": "pile"}
	_gesture("player", "push_bet", t, bm)
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
		_mark(card_id("player", (_seats["player"]["cards"] as Array).size() - 1), "cross", t)
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
	for n in NPCS:  # the others' stacks follow their own results
		match _game.result(n):
			"blackjack":
				_npc_chips[n] = mini(int(_npc_chips[n]) + 2, MAX_CHIPS)
			"win":
				_npc_chips[n] = mini(int(_npc_chips[n]) + 1, MAX_CHIPS)
			"lose", "bust":
				_npc_chips[n] = maxi(int(_npc_chips[n]) - 1, 1)
	if res == "blackjack" or res == "win":  # a tick on every card of the winning hand, a glow on the stack the payout goes to
		for i in (_seats["player"]["cards"] as Array).size():
			_mark(card_id("player", i), "tick", t)
		_mark("bj_chips_player", "glow", t)
	elif res == "push":
		_mark("bj_chips_player", "glow", t)
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


# the room: things, people, feedback, controls (CONTRACTS.md 10) ---------------------------------------------------------------------

## A feedback mark at a thing: logged, and asked of the room when there is one.
func _mark(thing: String, kind: String, t: float) -> void:
	feedback_log.append({"thing": thing, "kind": kind, "t": t})
	if world != null:
		world.feedback(thing, kind, t)


## The thing id of card `i` of `seat`.
static func card_id(seat: String, i: int) -> String:
	return "bj_card_%s_%d" % [seat, i]


## The chip sheet's frame for `pence` in `colour` (CHIP_COLOUR): the whole fivers as chips (at most MAX_CHIPS), a coin beside them when there are pence over.
static func chip_frame(pence: int, colour: int) -> int:
	var p := maxi(pence, 0)
	var change := 1 if p % CHIP_PENCE != 0 else 0
	return (colour * 2 + change) * (MAX_CHIPS + 1) + mini(p / CHIP_PENCE, MAX_CHIPS)


## The pence a chip frame shows (whole fivers; the coin says only that there is change): the inverse of chip_frame to the fiver.
static func chip_pence_of(frame: int) -> int:
	return (frame % (MAX_CHIPS + 1)) * CHIP_PENCE


## The card sheet's frame of a card ({rank, suit}) face up, or the back.
static func card_frame(card: Dictionary, up: bool) -> int:
	return int(card["suit"]) * 13 + int(card["rank"]) - 1 if up else BACK


## The people state of a seat's person from its gesture and mood at song time `t` (one of PEOPLE_STATES) and the song time it began: {state, t0}. A gesture under way
## wins (dealing, sweeping and paying are `deal`, a clap `clap`, pointing at the deck or a hand, asking for a card or waving one off `look`, a shrug `frown`, an invitation
## `happy`); else the mood (happy, laugh, surprised, smug: `happy`; annoyed, sad, wince, concerned: `frown`; thinking: `look`; else `idle`).
static func people_state_of(seat_state: Dictionary, t: float) -> Dictionary:
	var g: Dictionary = seat_state["gesture"]
	var m: Dictionary = seat_state["mood"]
	var g0 := float(g["t0"])
	var g1 := g0 + float(g["dur"])
	if float(g["dur"]) > 0.0 and t >= g0 and t < g1:
		var gs := ""
		match str(g["name"]):
			"deal", "sweep", "pay":
				gs = "deal"
			"clap":
				gs = "clap"
			"point_deck", "point_hand", "tap_table", "wave_off":
				gs = "look"
			"shrug":
				gs = "frown"
			"invite":
				gs = "happy"
		if gs != "":
			return {"state": gs, "t0": g0}
	var ms := "idle"
	match str(m["name"]):
		"happy", "laugh", "surprised", "smug":
			ms = "happy"
		"annoyed", "sad", "wince", "concerned":
			ms = "frown"
		"thinking":
			ms = "look"
	var since := float(m["t0"])
	if float(g["dur"]) > 0.0 and t >= g1:
		since = maxf(since, g1)
	return {"state": ms, "t0": minf(since, t)}


func _people_now() -> Dictionary:
	var out := {}
	for seat: String in ACTORS:
		out[seat] = people_state_of(_seats[seat], _now)
	return out


## Directs every person whose people state changed since the last call, from the song time it changed (never earlier than the last direction). Only while seated.
func _sync_people() -> void:
	if not began or _seats.is_empty() or _phase == "":
		return
	for seat: String in ACTORS:
		var p := people_state_of(_seats[seat], _now)
		var last: Dictionary = _people.get(seat, {})
		if not last.is_empty() and str(last["state"]) == str(p["state"]):
			continue
		var t0 := maxf(float(p["t0"]), float(last.get("t0", -INF)))
		_people[seat] = {"state": str(p["state"]), "t0": t0}
		people_log.append({"id": ACTORS[seat], "seat": seat, "state": str(p["state"]), "t": t0})
		if world != null:
			world.people(str(ACTORS[seat]), str(p["state"]), t0, 0.0)


## The controls in the pad slots: bet (a chip; a press in the betting window adds a step), twist (a card drawn off the deck), stick (a flat hand over the cards), get up
## (a door). Each draws itself (`draw`): bright while it can be pressed, dimmed otherwise, the bet's chips stacked as many as the hand's stake has steps.
func controls() -> Array:
	var out: Array = []
	for c: Array in [["bet", "chip"], ["deck", "card_draw"], ["hand", "flat_hand"], ["exit", "door"]]:
		var id: String = c[0]
		var pic: String = c[1]
		out.append({"id": id, "label": "", "pictogram": pic, "draw": func(ci: CanvasItem, face: Rect2, a: float) -> void: _draw_control(ci, id, pic, face, a)})
	return out


## Whether control `id` can be pressed now (the exit stands for the room's doors).
func control_live(id: String) -> bool:
	var tg := targets()
	if id == "exit":
		return tg.any(func(x: String) -> bool: return is_exit_target(x))
	return id in tg


func _draw_control(ci: CanvasItem, id: String, pic: String, face: Rect2, a: float) -> void:
	var live := control_live(id)
	var col := Color(1.0, 0.93, 0.72, a) if live else Color(0.62, 0.6, 0.66, a * 0.5)
	var ink := Color(0.02, 0.0, 0.08, 0.55 * a)
	var c := face.get_center() + Vector2(0, face.size.y * 0.04)
	var s := minf(face.size.x, face.size.y) * 0.2
	var n := 1
	if id == "bet" and _live:
		n = clampi(_stake / maxi(_step, 1), 1, _max_steps)
	for k in n:  # the bet's chips stack up with its steps
		var o := Vector2(0, -float(k) * s * 0.42)
		ControlPictograms.shape(ci, pic, c + o + Vector2(0, maxf(2.0, s * 0.08)), s, ink)
		ControlPictograms.shape(ci, pic, c + o, s, col)


## The table's things at the last song time: {id, sprite, at: [x, z], sector, size, frame, y}, in a fixed order: the deck, every card dealt and not yet cleared away (in seat
## order), the three chip stacks and the bet pile. Empty before the player sits and once the game is over.
func things() -> Array:
	if not began or _done or _phase == "":
		return []
	var out: Array = []
	var st: Dictionary = _stage
	var sec := str(st["sector"])
	var csz: Array = st["card"]
	var dk: Array = st["deck"]
	var deck := Vector3(float(dk[0]), float(dk[2]), float(dk[1]))  # x, y (height), z
	var t := _last
	out.append({"id": "bj_deck", "sprite": CARDS, "at": [deck.x, deck.z], "sector": sec, "size": csz, "frame": BACK, "y": deck.y})
	var clear_s := _b("clear")
	for seat: String in SEATS:
		var near := seat == "player"
		var z := float(st["near_z"] if near else st["far_z"])
		var y := float(st["near_y"] if near else st["far_y"])
		var x0 := float((st["cards_x"] as Dictionary)[seat])
		var cards: Array = _seats[seat]["cards"]
		for i in cards.size():
			var c: Dictionary = cards[i]
			var td := float(c["t_deal"])
			if t < td:
				continue
			var tc := float(c["t_clear"])
			if tc >= 0.0 and t >= tc + clear_s:
				continue
			var spot := Vector3(x0 + float(i) * float(st["fan"]), y, z + float(i) * 0.01)  # (a later card a centimetre nearer: drawn over the one before)
			var p := spot
			var tl := float(c["t_land"])
			if t < tl:  # dealt: sliding from the deck
				p = deck.lerp(spot, clampf((t - td) / maxf(tl - td, 1.0e-3), 0.0, 1.0))
			elif tc >= 0.0 and t >= tc:  # cleared: sliding back
				p = spot.lerp(deck, clampf((t - tc) / maxf(clear_s, 1.0e-3), 0.0, 1.0))
			var flip := float(c["t_flip"])
			var up := (bool(c["up"]) or (flip >= 0.0 and t >= flip)) and t >= tl
			out.append({"id": card_id(seat, i), "sprite": CARDS, "at": [p.x, p.z], "sector": sec, "size": csz, "frame": card_frame(c, up), "y": p.y})
	var chip: Array = st["chip"]
	var sx: Dictionary = st["stack_x"]
	var ny := float(st["near_y"]) - 0.04
	var fy := float(st["far_y"]) - 0.04
	out.append({"id": "bj_chips_player", "sprite": CHIPS, "at": [float(sx["player"]), float(st["near_z"]) + 0.05], "sector": sec, "size": chip,
		"frame": chip_frame(shown_pile_pence(t), CHIP_COLOUR["player"]), "y": ny})
	for n in NPCS:
		out.append({"id": "bj_chips_" + n, "sprite": CHIPS, "at": [float(sx[n]), float(st["far_z"])], "sector": sec, "size": chip,
			"frame": chip_frame(int(_npc_chips[n]) * CHIP_PENCE, CHIP_COLOUR[n]), "y": fy})
	out.append({"id": "bj_bet", "sprite": CHIPS, "at": [float(st["bet_x"]), float(st["near_z"]) + 0.05], "sector": sec, "size": chip,
		"frame": chip_frame(wallet.held_pence(), CHIP_COLOUR["bet"]), "y": ny})
	return out


## The pence the player's own stack shows at song time `t`: the wallet's balance, except while the money comes out of the pockets (sitting: it grows from nothing, a fiver at
## a time) and goes back into them (leaving: it shrinks to nothing), the wallet itself unchanged both times.
func shown_pile_pence(t: float) -> int:
	var bal: int = wallet.balance_pence()
	if str(_pile.get("via", "")) == "pockets" and (_phase == "sitting" or _phase == "leaving"):
		var k := clampf((t - float(_pile["t0"])) / maxf(float(_pile["dur"]), 1.0e-3), 0.0, 1.0)
		var to := bal if _phase == "sitting" else 0
		if k >= 1.0:
			return to
		var from := 0 if _phase == "sitting" else int(_pile["from"])
		return int(round(lerpf(float(from), float(to), k) / float(CHIP_PENCE))) * CHIP_PENCE
	return bal


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
