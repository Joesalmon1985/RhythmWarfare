class_name DuelMatch
extends RefCounted
## The duel's score book (no nodes, no clock). Side 0 is this player, side 1 the opponent. Each player plays the same phrase at
## the same time on their own phone, judges it themselves and reports one result per phrase: {j, cast, power10, ...}. When both
## results for phrase j are in, the spells land: each cast hits the other wizard for its power. Phrases resolve strictly in
## order, so two phones that see the same results always reach the same health and the same winner.
##
## The duel ends when a wizard reaches 0 (the one with more health left wins; equal and both down is a draw), or after
## max_phrases when the higher health wins. Equal health then goes to sudden death: play on until a phrase leaves them unequal.

var rules: DuelRules
var hp10: Array = [0, 0]  # health in tenths, never below 0
var raw10: Array = [0, 0]  # the same without the floor: how far past zero a knock-out went, so a double knock-out has a winner
var phrase := 0  # next phrase to resolve
var finished := false
var winner := -2  # -2 undecided, 0 or 1 the winner, -1 a draw
var reason := ""  # "ko", "time", "sudden", "draw", "forfeit"
var sudden_death := false
var total_credit: Array = [0.0, 0.0]
var casts: Array = [0, 0]
var history: Array = []  # [{j, hp10 (after), cast [bool, bool], power10 [int, int]}]

var _pending: Dictionary = {}  # j -> {0: result, 1: result}
var _events: Array = []


func _init(p_rules: DuelRules = null) -> void:
	if p_rules != null:
		setup(p_rules)


func setup(p_rules: DuelRules) -> void:
	rules = p_rules
	hp10 = [rules.max_hp10(), rules.max_hp10()]
	raw10 = hp10.duplicate()
	phrase = 0
	finished = false
	winner = -2
	reason = ""
	sudden_death = false
	total_credit = [0.0, 0.0]
	casts = [0, 0]
	history = []
	_pending = {}
	_events = []


## Records side `side`'s result for phrase `j` (a result is {j, cast, power10, credit, family}); returns the events that became due.
func submit(side: int, j: int, result: Dictionary) -> Array:
	if finished or j < phrase:
		return []
	if not _pending.has(j):
		_pending[j] = {}
	if (_pending[j] as Dictionary).has(side):
		return []  # a repeated message changes nothing
	_pending[j][side] = result
	while not finished and _pending.has(phrase) and (_pending[phrase] as Dictionary).size() == 2:
		_resolve(phrase)
		phrase += 1
	return drain()


## One side left the duel: the other wins.
func forfeit(side: int) -> Array:
	if finished:
		return []
	finished = true
	winner = 1 - side
	reason = "forfeit"
	_events.append({"kind": "end", "winner": winner, "reason": reason, "hp10": hp10.duplicate()})
	return drain()


func drain() -> Array:
	var out := _events
	_events = []
	return out


## Phrases that have both results waiting for earlier phrases are held back; this is how many results are waiting.
func waiting() -> int:
	return _pending.size()


func _resolve(j: int) -> void:
	var r: Dictionary = _pending[j]
	_pending.erase(j)
	var spells: Array = []
	var cast := [false, false]
	var power := [0, 0]
	for side in 2:
		var res: Dictionary = r[side]
		total_credit[side] += float(res.get("credit", 0.0))
		cast[side] = bool(res.get("cast", false))
		if cast[side]:
			power[side] = maxi(int(res.get("power10", 0)), 0)
			casts[side] += 1
			spells.append({"from": side, "to": 1 - side, "power10": power[side], "family": str(res.get("family", "drums"))})
	raw10[1] = int(raw10[1]) - int(power[0])
	raw10[0] = int(raw10[0]) - int(power[1])
	hp10[1] = maxi(int(raw10[1]), 0)
	hp10[0] = maxi(int(raw10[0]), 0)
	history.append({"j": j, "hp10": hp10.duplicate(), "cast": cast, "power10": power})
	_events.append({"kind": "phrase", "j": j, "spells": spells, "hp10": hp10.duplicate(), "results": [r[0], r[1]]})
	_check_end(j)


func _check_end(j: int) -> void:
	var h0 := int(raw10[0])
	var h1 := int(raw10[1])
	if h0 <= 0 or h1 <= 0:
		_end(0 if h0 > h1 else (1 if h1 > h0 else -1), "ko" if h0 != h1 else "draw")
		return
	var limit := int(rules.cfg["max_phrases"])
	if j + 1 < limit:
		return
	if h0 != h1:
		_end(0 if h0 > h1 else 1, "sudden" if sudden_death else "time")
		return
	if not sudden_death:
		sudden_death = true
		_events.append({"kind": "sudden_death", "j": j})
	if j + 1 >= limit + int(rules.cfg.get("sudden_death_extra", 16)):
		var c0: float = total_credit[0]
		var c1: float = total_credit[1]
		_end(0 if c0 > c1 + 1e-9 else (1 if c1 > c0 + 1e-9 else -1), "draw" if absf(c0 - c1) <= 1e-9 else "sudden")


func _end(w: int, why: String) -> void:
	finished = true
	winner = w
	reason = why
	_events.append({"kind": "end", "winner": w, "reason": why, "hp10": hp10.duplicate()})
