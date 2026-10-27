class_name Judge
extends RefCounted
## Input judgement (PRD section 4). Pure state machine over the chart's notes, driven by song time in seconds.
## Every note resolves exactly once. Rewards are queued as events for the battle to consume; they are never
## accumulated or deferred to phrase boundaries.
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
var _lane_notes: Dictionary = {}  # lane -> Array[int] note indexes in time order
var _lane_cursor: Dictionary = {}  # lane -> first index into _lane_notes that may still be unresolved
var _lane_available: Dictionary = {"kick": true, "snare": true, "bass": true}
var _active_hold: Dictionary = {}  # lane -> {"index": int, "touch": int}
var _events: Array = []
var _now := 0.0

var perfect := 0
var good := 0
var misses := 0
var strays := 0
var combo := 0
var best_combo := 0
var rewards := {"kick": 0, "snare": 0, "bass": 0}


func setup(chart_notes: Array) -> void:
	notes = chart_notes
	_state.resize(notes.size())
	_state.fill(State.UNJUDGED)
	for lane in Level.LANES:
		_lane_notes[lane] = []
		_lane_cursor[lane] = 0
	for i in notes.size():
		_lane_notes[notes[i]["lane"]].append(i)
	perfect = 0
	good = 0
	misses = 0
	strays = 0
	combo = 0
	best_combo = 0
	rewards = {"kick": 0, "snare": 0, "bass": 0}
	_active_hold.clear()
	_events.clear()
	_now = 0.0


func state_of(index: int) -> int:
	return _state[index]


func is_lane_available(lane: String) -> bool:
	return _lane_available[lane]


## Producer destroyed (kick/snare): future notes on the lane become UNAVAILABLE as they come up and presses are inert.
## The bass lane is never made unavailable: rebuilding is its recovery function.
func set_lane_available(lane: String, available: bool) -> void:
	if lane == "bass":
		return
	_lane_available[lane] = available


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
	for lane in Level.LANES:
		var list: Array = _lane_notes[lane]
		var cursor: int = _lane_cursor[lane]
		while cursor < list.size():
			var i: int = list[cursor]
			var n: Dictionary = notes[i]
			var st := _state[i]
			if st == State.UNJUDGED:
				if _now > n["time"] + good_s:
					if _lane_available[lane]:
						_resolve(i, State.MISS, "miss")
					else:
						_resolve(i, State.UNAVAILABLE, "unavailable")
				else:
					break
			elif st == State.HOLDING:
				if _now >= n["end_time"]:
					_complete_hold(lane, i, "hold_complete")
				else:
					break
			cursor += 1
		_lane_cursor[lane] = cursor


## A finger or key goes down on a lane. Returns the judgement dictionary that was also queued as an event.
func press(lane: String, now: float, touch_id: int = 0) -> Dictionary:
	update(now)
	if not _lane_available[lane]:
		return {"kind": "inert", "lane": lane}
	if _active_hold.has(lane):
		# A second finger on a lane that is already holding cannot satisfy anything: ignore it (no stray, no reward).
		return {"kind": "ignored", "lane": lane}
	var best := -1
	var best_delta := INF
	for i in _lane_notes[lane].slice(_lane_cursor[lane]):
		if _state[i] != State.UNJUDGED:
			continue
		var n: Dictionary = notes[i]
		var delta: float = now - n["time"]
		if delta > good_s:
			continue
		if delta < -good_s:
			break  # notes are in time order; nothing later can match
		# Nearest eligible note wins; on an exact tie the earlier note wins because the scan is in time order
		# and only a strictly smaller distance replaces the candidate.
		if absf(delta) < best_delta:
			best = i
			best_delta = absf(delta)
	if best < 0:
		strays += 1
		combo = 0
		var stray := {"kind": "stray", "lane": lane, "time": now}
		_events.append(stray)
		return stray
	var note: Dictionary = notes[best]
	var kind := "perfect" if best_delta <= perfect_s else "good"
	var delta_ms: float = (now - float(note["time"])) * 1000.0
	if note["type"] == "hold":
		_state[best] = State.HOLDING
		_active_hold[lane] = {"index": best, "touch": touch_id, "kind": kind, "delta_ms": delta_ms}
		var started := {"kind": "hold_start", "judgement": kind, "lane": lane, "note_id": note["id"], "index": best, "time": now, "delta_ms": delta_ms}
		_events.append(started)
		return started
	return _hit(best, kind, now, delta_ms)


## The finger or key leaves the lane.
func release(lane: String, now: float, touch_id: int = 0) -> Dictionary:
	update(now)
	if not _active_hold.has(lane):
		return {"kind": "none", "lane": lane}
	var hold: Dictionary = _active_hold[lane]
	if hold["touch"] != touch_id:
		return {"kind": "ignored", "lane": lane}
	var i: int = hold["index"]
	if _state[i] != State.HOLDING:
		_active_hold.erase(lane)
		return {"kind": "none", "lane": lane}
	var n: Dictionary = notes[i]
	if now >= n["end_time"] - hold_tolerance_s:
		# Released inside the tolerance: the reward still resolves at the scheduled tail, not now.
		return {"kind": "hold_release_ok", "lane": lane, "note_id": n["id"]}
	_active_hold.erase(lane)
	_resolve(i, State.MISS, "hold_fail")
	return {"kind": "hold_fail", "lane": lane, "note_id": n["id"]}


## Pause interrupts an active hold: it is voided with no reward and no penalty (PRD section 8).
func void_active_holds() -> void:
	for lane in _active_hold.keys():
		var i: int = _active_hold[lane]["index"]
		if _state[i] == State.HOLDING:
			_state[i] = State.VOID
			_events.append({"kind": "void", "lane": lane, "note_id": notes[i]["id"], "index": i})
	_active_hold.clear()


func active_hold_progress(lane: String) -> float:
	if not _active_hold.has(lane):
		return -1.0
	var n: Dictionary = notes[_active_hold[lane]["index"]]
	var span: float = n["end_time"] - n["time"]
	return 0.0 if span <= 0.0 else clampf((_now - n["time"]) / span, 0.0, 1.0)


func _complete_hold(lane: String, i: int, _why: String) -> void:
	var kind: String = _active_hold[lane]["kind"] if _active_hold.has(lane) else "good"
	var delta: float = float(_active_hold[lane].get("delta_ms", 0.0)) if _active_hold.has(lane) else 0.0
	_active_hold.erase(lane)
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
	rewards[n["lane"]] += 1
	var ev := {"kind": kind, "lane": n["lane"], "note_id": n["id"], "index": i, "tick": n["tick"], "time": at, "reward": true, "delta_ms": delta_ms}
	_events.append(ev)
	return ev


func _resolve(i: int, state: int, kind: String) -> void:
	var n: Dictionary = notes[i]
	_state[i] = state
	if state == State.MISS:
		misses += 1
		combo = 0
	_events.append({"kind": kind, "lane": n["lane"], "note_id": n["id"], "index": i, "tick": n["tick"]})
