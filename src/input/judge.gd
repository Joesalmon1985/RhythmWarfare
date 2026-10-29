class_name Judge
extends RefCounted
## Input judgement (PRD section 4). Pure state machine over the chart's notes, driven by song time in seconds.
## Every note resolves exactly once. Rewards are queued as events for the battle to consume; they are never
## accumulated or deferred to phrase boundaries.
##
## Presses arrive per button (1 to 4). A note's button says where it is played; its slot_id says what it rewards
## and whether it is still available. In schema 1 packs the slot id is the lane (a destroyed war factory makes
## kick notes unavailable, a destroyed barracks snare notes; bass notes never become unavailable). In schema 2
## packs every equipped slot has its own availability, set by the match from the slot's producers. A note's button
## never decides what it rewards, so one button can carry kick taps in one phrase and bass holds in the next.
##
## Note states: UNJUDGED -> HIT | MISS | UNAVAILABLE | VOID, with HOLDING as the transient state of a bass hold.

enum State { UNJUDGED, HOLDING, HIT, MISS, UNAVAILABLE, VOID }

const PERFECT_MS := 45.0
const GOOD_MS := 100.0
const HOLD_RELEASE_TOLERANCE_MS := 60.0

var perfect_s := PERFECT_MS / 1000.0
var good_s := GOOD_MS / 1000.0
var hold_tolerance_s := HOLD_RELEASE_TOLERANCE_MS / 1000.0

var notes: Array = []  # chart notes (dictionaries from Level), sorted by tick
var _state: Array[int] = []
var _button_notes: Dictionary = {}  # button -> Array[int] note indexes in time order
var _button_cursor: Dictionary = {}  # button -> first index into _button_notes that may still be unresolved
var _slot_available: Dictionary = {}  # slot id -> bool; a slot not listed is available
var _active_hold: Dictionary = {}  # button -> {"index": int, "touch": int, "kind", "delta_ms"}
var _events: Array = []
var _now := 0.0

var perfect := 0
var good := 0
var misses := 0
var strays := 0
var combo := 0
var best_combo := 0
var rewards := {"kick": 0, "snare": 0, "bass": 0}  # reward count per slot id


func setup(chart_notes: Array) -> void:
	notes = chart_notes
	_state.resize(notes.size())
	_state.fill(State.UNJUDGED)
	_button_notes.clear()
	_button_cursor.clear()
	for b in range(1, Level.BUTTONS + 1):
		_button_notes[b] = []
		_button_cursor[b] = 0
	for n in notes:  # hand-built notes (tests, schema 1) carry a lane only: the lane is their slot
		if not n.has("slot_id"):
			n["slot_id"] = n.get("lane", "")
		if not n.has("lane"):
			n["lane"] = n.get("family", n["slot_id"])
		n["part_id"] = n.get("part_id", n["slot_id"])
		n["source_note_id"] = n.get("source_note_id", "")
	for i in notes.size():
		var b := int(notes[i].get("button", Level.FIXED_BUTTON.get(notes[i].get("lane", ""), 2)))
		if not _button_notes.has(b):
			_button_notes[b] = []
			_button_cursor[b] = 0
		_button_notes[b].append(i)
	perfect = 0
	good = 0
	misses = 0
	strays = 0
	combo = 0
	best_combo = 0
	rewards = {"kick": 0, "snare": 0, "bass": 0}
	_slot_available = {}
	_active_hold.clear()
	_events.clear()
	_now = 0.0


func state_of(index: int) -> int:
	return _state[index]


func is_slot_available(slot: String) -> bool:
	return _slot_available.get(slot, true)


## Producer gone: future notes of the slot become UNAVAILABLE as they come up and presses on them are inert.
func set_slot_available(slot: String, available: bool) -> void:
	_slot_available[slot] = available


func is_lane_available(lane: String) -> bool:
	return is_slot_available(lane)


## Schema 1: the bass lane is never made unavailable (rebuilding a pad is its recovery function).
func set_lane_available(lane: String, available: bool) -> void:
	if lane == "bass":
		return
	set_slot_available(lane, available)


## Counted notes exclude UNAVAILABLE and VOID ones (they never required an input).
func judged_count() -> int:
	return perfect + good + misses


func accuracy() -> float:
	var n := judged_count()
	return 1.0 if n == 0 else float(perfect + good) / float(n)


func drain_events() -> Array:
	var out := _events
	_events = []
	return out


## Advance the clock: expire missed notes, resolve completed holds. Call every frame before handling input.
func update(now: float) -> void:
	_now = maxf(_now, now)
	for button in _button_notes:
		var list: Array = _button_notes[button]
		var cursor: int = _button_cursor[button]
		while cursor < list.size():
			var i: int = list[cursor]
			var n: Dictionary = notes[i]
			var st := _state[i]
			if st == State.UNJUDGED:
				if _now > n["time"] + good_s:
					if is_slot_available(n["slot_id"]):
						_resolve(i, State.MISS, "miss")
					else:
						_resolve(i, State.UNAVAILABLE, "unavailable")
				else:
					break
			elif st == State.HOLDING:
				if _now >= n["end_time"]:
					_complete_hold(button, i, "hold_complete")
				else:
					break
			cursor += 1
		_button_cursor[button] = cursor


## A finger or key goes down on a button. Returns the judgement dictionary that was also queued as an event.
func press(button: int, now: float, touch_id: int = 0) -> Dictionary:
	update(now)
	if not _button_notes.has(button):
		return {"kind": "ignored", "button": button}
	if _active_hold.has(button):
		# A second finger on a button that is already holding cannot satisfy anything: ignore it (no stray, no reward).
		return {"kind": "ignored", "button": button}
	var best := -1
	var best_delta := INF
	var unavailable_in_window := false
	for i in _button_notes[button].slice(_button_cursor[button]):
		if _state[i] != State.UNJUDGED:
			continue
		var n: Dictionary = notes[i]
		var delta: float = now - n["time"]
		if delta > good_s:
			continue
		if delta < -good_s:
			break  # notes are in time order; nothing later can match
		if not is_slot_available(n["slot_id"]):
			unavailable_in_window = true
			continue
		# Nearest eligible note wins; on an exact tie the earlier note wins because the scan is in time order
		# and only a strictly smaller distance replaces the candidate.
		if absf(delta) < best_delta:
			best = i
			best_delta = absf(delta)
	if best < 0:
		if unavailable_in_window:
			# the press landed on a note whose producer is gone: inert, not a stray
			return {"kind": "inert", "button": button}
		strays += 1
		combo = 0
		var stray := {"kind": "stray", "button": button, "time": now}
		_events.append(stray)
		return stray
	var note: Dictionary = notes[best]
	var kind := "perfect" if best_delta <= perfect_s else "good"
	var delta_ms: float = (now - float(note["time"])) * 1000.0
	if note["type"] == "hold":
		_state[best] = State.HOLDING
		_active_hold[button] = {"index": best, "touch": touch_id, "kind": kind, "delta_ms": delta_ms}
		var started := {"kind": "hold_start", "judgement": kind, "lane": note["lane"], "slot_id": note["slot_id"], "button": button, "note_id": note["id"], "index": best, "time": now, "delta_ms": delta_ms}
		_events.append(started)
		return started
	return _hit(best, kind, now, delta_ms)


## The finger or key leaves the button.
func release(button: int, now: float, touch_id: int = 0) -> Dictionary:
	update(now)
	if not _active_hold.has(button):
		return {"kind": "none", "button": button}
	var hold: Dictionary = _active_hold[button]
	if hold["touch"] != touch_id:
		return {"kind": "ignored", "button": button}
	var i: int = hold["index"]
	if _state[i] != State.HOLDING:
		_active_hold.erase(button)
		return {"kind": "none", "button": button}
	var n: Dictionary = notes[i]
	if now >= n["end_time"] - hold_tolerance_s:
		# Released inside the tolerance: the reward still resolves at the scheduled tail, not now.
		return {"kind": "hold_release_ok", "lane": n["lane"], "slot_id": n["slot_id"], "button": button, "note_id": n["id"]}
	_active_hold.erase(button)
	_resolve(i, State.MISS, "hold_fail")
	return {"kind": "hold_fail", "lane": n["lane"], "slot_id": n["slot_id"], "button": button, "note_id": n["id"]}


## Pause interrupts an active hold: it is voided with no reward and no penalty (PRD section 8).
func void_active_holds() -> void:
	for button in _active_hold.keys():
		var i: int = _active_hold[button]["index"]
		if _state[i] == State.HOLDING:
			_state[i] = State.VOID
			_events.append({"kind": "void", "lane": notes[i]["lane"], "slot_id": notes[i]["slot_id"], "button": button, "note_id": notes[i]["id"], "index": i})
	_active_hold.clear()


func active_hold_progress(button: int) -> float:
	if not _active_hold.has(button):
		return -1.0
	var n: Dictionary = notes[_active_hold[button]["index"]]
	var span: float = n["end_time"] - n["time"]
	return 0.0 if span <= 0.0 else clampf((_now - n["time"]) / span, 0.0, 1.0)


func _complete_hold(button: int, i: int, _why: String) -> void:
	var kind: String = _active_hold[button]["kind"] if _active_hold.has(button) else "good"
	var delta: float = float(_active_hold[button].get("delta_ms", 0.0)) if _active_hold.has(button) else 0.0
	_active_hold.erase(button)
	_hit(i, kind, notes[i]["end_time"], delta)


func _hit(i: int, kind: String, at: float, delta_ms: float = 0.0) -> Dictionary:
	var n: Dictionary = notes[i]
	_state[i] = State.HIT
	if kind == "perfect":
		perfect += 1
	else:
		good += 1
	combo += 1
	best_combo = maxi(best_combo, combo)
	rewards[n["slot_id"]] = int(rewards.get(n["slot_id"], 0)) + 1
	var ev := {"kind": kind, "lane": n["lane"], "slot_id": n["slot_id"], "part_id": n["part_id"], "source_note_id": n["source_note_id"], "button": int(n["button"]), "note_id": n["id"], "index": i, "tick": n["tick"], "time": at, "reward": true, "delta_ms": delta_ms}
	_events.append(ev)
	return ev


func _resolve(i: int, state: int, kind: String) -> void:
	var n: Dictionary = notes[i]
	_state[i] = state
	if state == State.MISS:
		misses += 1
		combo = 0
	_events.append({"kind": kind, "lane": n["lane"], "slot_id": n["slot_id"], "button": int(n["button"]), "note_id": n["id"], "index": i, "tick": n["tick"]})
