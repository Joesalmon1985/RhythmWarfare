class_name TrialFlow
extends RefCounted
## The dungeon's rules with no nodes: which passage the player is in, what they may choose, what happens when a phrase is passed or failed. The scene feeds it
## choices and phrase results; nothing else (no free movement, no menus) can change it.
##
##   SCENE   a passage is shown with its choices (a consequence line when the player has just passed a phrase)
##   PHRASE  a choice with a phrase was selected: the four pads play it
##   ENDED   the player left through an exit choice
##
## A passed phrase moves to the choice's passage and keeps the choice's consequence text; a failed one stays in the passage with the same choices, the chosen
## one marked as a retry. A choice with an encounter is a fight: the result also names the outcome animation ("win" or "lose").

enum State { SCENE, PHRASE, ENDED }

var data: TrialData
var state := State.SCENE
var passage := 1
var consequence := ""  # what the last pass led to, shown with the new passage
var failure := ""  # what the last failed phrase cost, shown with the same choices
var retry_index := -1  # the choice index that was failed last (marked "try again")
var selected := -1
var attempts := 0  # failed attempts on the current selection
var history: Array = []  # [{passage, choice, result}]
var visited: Array = []
var exit := ""  # set when the player leaves ("warehouse")
var rejoined: Array = []  # passages entered more than once (routes that rejoin)
var flags: Array = []  # items the player carries (ids from the data's "items"); a passage "grants" them on entry and a choice may "require" one
var gained := ""  # the item picked up on entering the current passage ("" when none)


func _init(p_data: TrialData = null, start_passage: int = -1, carried: Array = []) -> void:
	if p_data != null:
		begin(p_data, start_passage, carried)


## `carried`: the items the player had when they last left the dungeon (the narrative router's saved progress, work package N2.2): held again from the first passage.
func begin(p_data: TrialData, start_passage: int = -1, carried: Array = []) -> void:
	data = p_data
	state = State.SCENE
	passage = start_passage if start_passage >= 0 and data.passages.has(start_passage) else data.start
	consequence = ""
	failure = ""
	retry_index = -1
	selected = -1
	attempts = 0
	history = []
	visited = [passage]
	rejoined = []
	flags = []
	for it in carried:
		if data.items.has(str(it)) and not flags.has(str(it)):
			flags.append(str(it))
	gained = ""
	exit = ""
	_collect()


## The choices on offer now: those the player's items allow. Indexes into this list are what select() and the engine use.
func choices() -> Array:
	return data.choices_for(passage, flags)


## Picks up what the current passage grants (an item already held is not announced twice).
func _collect() -> void:
	gained = ""
	for g in current().get("grants", []):
		if str(g) not in flags:
			flags.append(str(g))
			gained = str(data.items.get(str(g), g))


func current() -> Dictionary:
	return data.passage(passage)


func is_endpoint() -> bool:
	return bool(current().get("endpoint", false))


## The player selects choice `i`. Returns {kind: "phrase", phrase, choice, encounter} when a phrase must be played, {kind: "move"} when the choice needs none
## (the passage changed), {kind: "exit"} when it leaves the dungeon, or {kind: "ignored"}.
func select(i: int) -> Dictionary:
	if state != State.SCENE or i < 0 or i >= choices().size():
		return {"kind": "ignored"}
	var c: Dictionary = choices()[i]
	selected = i
	if c.get("phrase", null) == null:
		if c.get("to", null) == null:
			exit = str(c.get("exit", ""))
			state = State.ENDED
			history.append({"passage": passage, "choice": i, "result": "exit"})
			return {"kind": "exit", "exit": exit}
		_move(c)
		return {"kind": "move"}
	state = State.PHRASE
	return {"kind": "phrase", "phrase": data.phrases[str(c["phrase"])], "phrase_id": str(c["phrase"]), "choice": c, "encounter": str(c.get("encounter", ""))}


## The phrase was played: `passed` and its credit. Returns {kind: "pass"|"fail", fight: bool, outcome: "win"|"lose"|"", text}.
func phrase_done(passed: bool, credit: float) -> Dictionary:
	if state != State.PHRASE:
		return {"kind": "ignored"}
	var c: Dictionary = choices()[selected]
	var fight := str(c.get("encounter", "")) != ""
	var enc: Dictionary = data.encounters.get(str(c.get("encounter", "")), {})
	state = State.SCENE
	if c.has("test"):  # a luck test: the rhythm decides which way it goes, and there is no second go
		var dest := int(c["test"]["pass" if passed else "fail"])
		history.append({"passage": passage, "choice": selected, "result": "pass" if passed else "fail", "credit": credit, "to": dest})
		attempts = 0
		retry_index = -1
		failure = ""
		var moved := c.duplicate()
		moved["to"] = dest
		_move(moved)
		consequence = (str(c.get("consequence", "")) if passed and str(c.get("consequence", "")) != "" else ("Luck is with you." if passed else "Luck turns against you.")) + _gain_note()
		return {"kind": "pass" if passed else "fail", "fight": false, "outcome": "", "text": consequence, "defeated": false}
	if passed:
		history.append({"passage": passage, "choice": selected, "result": "pass", "credit": credit})
		attempts = 0
		retry_index = -1
		failure = ""
		_move(c)
		if fight:
			consequence = ("%s %s" % [str(enc.get("on_win", "")), str(c.get("consequence", ""))]).strip_edges() + _gain_note()
		return {"kind": "pass", "fight": fight, "outcome": "win" if fight else "", "text": consequence, "defeated": false}
	history.append({"passage": passage, "choice": selected, "result": "fail", "credit": credit})
	attempts += 1
	if fight and int(c.get("lives", 0)) > 0 and attempts >= int(c["lives"]):  # beaten three times: the fight is lost for good, and the adventure with it
		var lost := {"to": 0, "consequence": str(enc.get("on_defeat", "The fight is lost. Your adventure ends here."))}
		attempts = 0
		retry_index = -1
		failure = ""
		_move(lost)
		return {"kind": "fail", "fight": true, "outcome": "lose", "text": consequence, "defeated": true}
	retry_index = selected
	failure = str(enc.get("on_fail", "")) if fight else "The moment slips. Try again."
	consequence = ""
	return {"kind": "fail", "fight": fight, "outcome": "lose" if fight else "", "text": failure, "defeated": false}


func _move(c: Dictionary) -> void:
	var to := int(c["to"])
	history.append({"passage": passage, "choice": selected, "result": "move", "to": to})
	if to in visited and to not in rejoined:
		rejoined.append(to)
	passage = to
	if to not in visited:
		visited.append(to)
	consequence = str(c.get("consequence", ""))
	_collect()
	consequence = (consequence + _gain_note()).strip_edges()
	selected = -1
	state = State.SCENE


func _gain_note() -> String:
	return (" You now carry %s." % gained) if gained != "" else ""
