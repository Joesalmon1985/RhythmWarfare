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


func _init(p_data: TrialData = null, start_passage: int = -1) -> void:
	if p_data != null:
		begin(p_data, start_passage)


func begin(p_data: TrialData, start_passage: int = -1) -> void:
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
	exit = ""


func choices() -> Array:
	return data.choices(passage)


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
		consequence = "Luck is with you." if passed else "Luck turns against you."
		return {"kind": "pass" if passed else "fail", "fight": false, "outcome": "", "text": consequence, "defeated": false}
	if passed:
		history.append({"passage": passage, "choice": selected, "result": "pass", "credit": credit})
		attempts = 0
		retry_index = -1
		failure = ""
		_move(c)
		if fight:
			consequence = "%s %s" % [str(enc.get("on_win", "")), str(c.get("consequence", ""))]
		return {"kind": "pass", "fight": fight, "outcome": "win" if fight else "", "text": consequence, "defeated": false}
	history.append({"passage": passage, "choice": selected, "result": "fail", "credit": credit})
	attempts += 1
	if fight and int(c.get("lives", 0)) > 0 and attempts >= int(c["lives"]):  # beaten three times: the fight is lost for good, and the adventure with it
		var lost := {"to": 0, "consequence": "The %s is too much for you. Your adventure ends here." % str(enc.get("name", "creature")).to_lower()}
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
	selected = -1
	state = State.SCENE
