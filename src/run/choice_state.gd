class_name ChoiceState
extends RefCounted
## The state of every choice on show (contract 9: idle, available, selected, committed, declined, cost), driven by the run's own events as the choice layer reads them
## (RunPlay.choice_state / TrialScene.choice_state: the staged options, the current one, the commit, the touch times) and the hotspot items (a commit's outcome, a refused tap).
## No clock of its own: every change is stamped with the song time of the event that caused it (a touch, a commit), so the same taps give the same states at any frame step.
##   staged and nothing touched or committed     available (the current one, the touched one or else the default, is selected: what happens if the player does nothing more)
##   touched                                      selected at once, stamped with the touch's song time (the response within 0.1 s is the next frame)
##   the lock passed (window_closed)              the others declined; the selected one stays selected through the lock
##   the commit (at the boundary, as today)        the chosen one committed (success) or cost (a failed outcome), the others declined
##   no longer staged                              forgotten (idle)

const STATES: Array = ContractShapes.CHOICE_STATES

var _mem: Dictionary = {}  # id -> {state, t_state, prev}
var _success: Dictionary = {}  # committed id -> success, as the items last said it


## The state of `id` for a choice snapshot `c` ({staged, current, committed, ...}): ContractShapes.choice_state with the run's words.
static func state_in(id: String, c: Dictionary, success := true, window_closed := false) -> String:
	var on_show := false
	for h in c.get("staged", []):
		if str(h["id"]) == id:
			on_show = true
	var committed := str(c.get("committed", ""))
	var sel := str(c.get("current", "")) if committed == "" else ""
	return ContractShapes.choice_state(id, on_show, sel, committed, success, window_closed)


## Whether the lock has passed: the snapshot says so (`window_closed`), else no staged final-window option is on show in `items` any more while nothing is committed
## (RunPlay.hotspot_items lists a final-window choice only while selection is open, from the scene's first beat to the lock; while the card table seats the player it lists
## nothing, and the doors step back too). `items` null: not known (nothing is inferred).
static func window_closed_of(c: Dictionary, items: Variant) -> bool:
	if c.has("window_closed"):
		return bool(c["window_closed"])
	if str(c.get("committed", "")) != "" or typeof(items) != TYPE_ARRAY:
		return false
	var on := {}
	for e in items:
		if str(e.get("state", "")) in ["available", "selected"]:
			on[str((e["hotspot"] as Dictionary).get("id", ""))] = true
	for h in c.get("staged", []):
		if RunHotspots.window_of(h) == "final" and on.has(str(h["id"])):
			return false
	return true


## Advance to the snapshot `c` at song time `t`; `items`: the hotspot items of this frame (a commit's success, refused taps; null when there are none to read).
## Returns {id: {state, t_state, prev, refused_t}}.
func update(c: Dictionary, t: float, items: Variant = null) -> Dictionary:
	var refused := {}
	for e in (items if typeof(items) == TYPE_ARRAY else []):
		var hid := str((e.get("hotspot", {}) as Dictionary).get("id", ""))
		match str(e.get("state", "")):
			"committed":
				_success[hid] = bool(e.get("success", true))
			"refused":
				refused[hid] = float(e.get("t_state", t))
	var closed := window_closed_of(c, items)
	var committed := str(c.get("committed", ""))
	var t_ch := float(c.get("changed_t", -INF))
	t_ch = minf(t_ch, t) if is_finite(t_ch) else t
	var touched: Dictionary = c.get("touched", {})
	var out := {}
	for h in c.get("staged", []):
		var id := str(h["id"])
		var st := state_in(id, c, bool(_success.get(committed, true)), closed)
		var m: Dictionary = _mem.get(id, {})
		if m.is_empty():  # first seen: already in its state (a scene begins with its doors where they belong)
			m = {"state": st, "t_state": -INF, "prev": ""}
		elif str(m["state"]) != st:
			var when := t_ch
			if st == "selected" and touched.has(id):
				when = minf(float(touched[id]), t)
			elif st == "declined" and committed == "":  # (the lock: no event of its own)
				when = t
			m = {"state": st, "t_state": maxf(when, float(m["t_state"])), "prev": str(m["state"])}
		_mem[id] = m
		var o: Dictionary = m.duplicate()
		o["refused_t"] = float(refused.get(id, -INF))
		out[id] = o
	for id in _mem.keys():
		if not out.has(id):
			_mem.erase(id)
	if committed == "":
		_success = {}
	return out


func clear() -> void:
	_mem = {}
	_success = {}
