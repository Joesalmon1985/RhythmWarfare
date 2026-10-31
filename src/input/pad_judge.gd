class_name PadJudge
extends RefCounted
## Cue recognition on the four pads (missions, PRD section 15). Pure state machine over the cues, driven by song time.
##
## A press is matched to the nearest unresolved cue of that pad inside the accept window; one press resolves at most one
## cue, a pad that is already held ignores further fingers, and a press with no cue in reach is a stray (it costs
## precision, never a cue). Taps resolve as perfect, great or ok (all accepted) or miss when the window closes. A hold
## starts like a tap and earns coverage: completed (released within the tolerance of its tail, or still held there)
## counts 1, an earlier release ends its contribution at held time / length. A hold never fails by being released.
##
## Every cue resolves exactly once, with a deterministic resolution time (the press, the release, the tail, or the end
## of the window), so the sequences built on top resolve the same at any frame rate.

enum State { PENDING, HOLDING, DONE }

var notes: Array = []
var accept_s := MissionRules.window_s("accept")
var perfect_s := MissionRules.window_s("perfect")
var great_s := MissionRules.window_s("great")
var complete_s := MissionRules.hold_complete_s()

var _state: Array[int] = []
var credit: PackedFloat32Array = PackedFloat32Array()  # per cue, 0..1, final once resolved
var delta_ms: PackedFloat32Array = PackedFloat32Array()  # onset error of accepted cues (NAN when missed)
var resolved_at: PackedFloat64Array = PackedFloat64Array()  # song time the cue's result became final
var _pad_notes: Dictionary = {}
var _cursor: Dictionary = {}
var _active: Dictionary = {}  # pad -> {index, touch}
var _events: Array = []
var _now := -INF
var sequences: Array = []  # [{index, start_time, end_time}] for stray attribution
var strays_by_seq: Dictionary = {}

var perfect := 0
var great := 0
var ok := 0
var misses := 0
var strays := 0
var holds_complete := 0
var holds_partial := 0
var combo := 0
var best_combo := 0


func setup(cues: Array, p_sequences: Array = []) -> void:
	notes = cues
	sequences = p_sequences
	var n := notes.size()
	_state.resize(n)
	_state.fill(State.PENDING)
	credit.resize(n)
	credit.fill(0.0)
	delta_ms.resize(n)
	delta_ms.fill(NAN)
	resolved_at.resize(n)
	resolved_at.fill(-1.0)
	_pad_notes = {1: [], 2: [], 3: [], 4: []}
	_cursor = {1: 0, 2: 0, 3: 0, 4: 0}
	for i in n:
		var pad := int(notes[i]["pad"])
		if not _pad_notes.has(pad):
			_pad_notes[pad] = []
			_cursor[pad] = 0
		_pad_notes[pad].append(i)
	_active.clear()
	_events.clear()
	strays_by_seq.clear()
	perfect = 0
	great = 0
	ok = 0
	misses = 0
	strays = 0
	holds_complete = 0
	holds_partial = 0
	combo = 0
	best_combo = 0
	_now = -INF


func is_resolved(i: int) -> bool:
	return _state[i] == State.DONE


func drain_events() -> Array:
	var out := _events
	_events = []
	return out


func accepted() -> int:
	return perfect + great + ok


## Share of resolved cues that were accepted (taps hit, holds started).
func accuracy() -> float:
	var n := accepted() + misses
	return 1.0 if n == 0 else float(accepted()) / float(n)


func update(now: float) -> void:
	_now = maxf(_now, now)
	for pad in _pad_notes:
		var list: Array = _pad_notes[pad]
		var c: int = _cursor[pad]
		while c < list.size():
			var i: int = list[c]
			var n: Dictionary = notes[i]
			if _state[i] == State.PENDING:
				if _now > float(n["time"]) + accept_s:
					_miss(i)
				else:
					break
			elif _state[i] == State.HOLDING:
				if _now >= float(n["end_time"]):
					_finish_hold(pad, i, float(n["end_time"]), true)
				else:
					break
			c += 1
		_cursor[pad] = c


func press(pad: int, now: float, touch_id: int = 0) -> Dictionary:
	update(now)
	if not _pad_notes.has(pad):
		return {"kind": "ignored", "pad": pad}
	if _active.has(pad):
		var held: Dictionary = notes[_active[pad]["index"]]
		if now < float(held["end_time"]) - complete_s:
			return {"kind": "ignored", "pad": pad}  # a second finger on a held pad satisfies nothing
		_finish_hold(pad, int(_active[pad]["index"]), now, true)  # a re-press at the tail completes the hold first
	var best := -1
	var best_abs := INF
	var list: Array = _pad_notes[pad]
	for k in range(_cursor[pad], list.size()):
		var i: int = list[k]
		if _state[i] != State.PENDING:
			continue
		var d: float = now - float(notes[i]["time"])
		if d > accept_s:
			continue
		if d < -accept_s:
			break
		if absf(d) < best_abs:  # nearest wins; on a tie the earlier cue (scan order)
			best = i
			best_abs = absf(d)
	if best < 0:
		strays += 1
		combo = 0
		var seq := _seq_at(now)
		if seq >= 0:
			strays_by_seq[seq] = int(strays_by_seq.get(seq, 0)) + 1
		var ev := {"kind": "stray", "pad": pad, "time": now, "seq": seq}
		_events.append(ev)
		return ev
	var n: Dictionary = notes[best]
	var dms := (now - float(n["time"])) * 1000.0
	var grade := "perfect" if best_abs <= perfect_s else ("great" if best_abs <= great_s else "ok")
	match grade:
		"perfect":
			perfect += 1
		"great":
			great += 1
		_:
			ok += 1
	combo += 1
	best_combo = maxi(best_combo, combo)
	delta_ms[best] = dms
	if n["type"] == "hold":
		_state[best] = State.HOLDING
		_active[pad] = {"index": best, "touch": touch_id}
		var hs := {"kind": "hold_start", "grade": grade, "pad": pad, "index": best, "seq": int(n["seq"]), "time": now, "delta_ms": dms}
		_events.append(hs)
		return hs
	_state[best] = State.DONE
	credit[best] = 1.0
	resolved_at[best] = now
	var ev := {"kind": grade, "pad": pad, "index": best, "seq": int(n["seq"]), "time": now, "delta_ms": dms}
	_events.append(ev)
	return ev


func release(pad: int, now: float, touch_id: int = 0) -> Dictionary:
	update(now)
	if not _active.has(pad):
		return {"kind": "none", "pad": pad}
	var a: Dictionary = _active[pad]
	if int(a["touch"]) != touch_id:
		return {"kind": "ignored", "pad": pad}
	var i: int = a["index"]
	var n: Dictionary = notes[i]
	return _finish_hold(pad, i, now, now >= float(n["end_time"]) - complete_s)


## Pause ends every active hold where it stands (coverage so far, nothing more), as a release would.
func pause_interrupt(now: float) -> void:
	update(now)  # a tail already passed completes normally first
	for pad in _active.keys():
		var i: int = _active[pad]["index"]
		_finish_hold(pad, i, now, false)


## Fraction of the active hold's span that has passed (for drawing), -1 when the pad holds nothing.
func hold_progress(pad: int, now: float) -> float:
	if not _active.has(pad):
		return -1.0
	var n: Dictionary = notes[_active[pad]["index"]]
	var span: float = float(n["end_time"]) - float(n["time"])
	return 1.0 if span <= 0.0 else clampf((now - float(n["time"])) / span, 0.0, 1.0)


func is_holding(pad: int) -> bool:
	return _active.has(pad)


func _finish_hold(pad: int, i: int, at: float, complete: bool) -> Dictionary:
	_active.erase(pad)
	var n: Dictionary = notes[i]
	var span: float = float(n["end_time"]) - float(n["time"])
	var cov := 1.0 if complete else (clampf((at - float(n["time"])) / span, 0.0, 1.0) if span > 0.0 else 1.0)
	_state[i] = State.DONE
	credit[i] = cov
	resolved_at[i] = minf(at, float(n["end_time"]))
	if complete:
		holds_complete += 1
	else:
		holds_partial += 1
	var ev := {"kind": "hold_complete" if complete else "hold_partial", "pad": pad, "index": i, "seq": int(n["seq"]),
		"time": resolved_at[i], "coverage": cov}
	_events.append(ev)
	return ev


func _miss(i: int) -> void:
	var n: Dictionary = notes[i]
	_state[i] = State.DONE
	credit[i] = 0.0
	resolved_at[i] = float(n["time"]) + accept_s
	misses += 1
	combo = 0
	_events.append({"kind": "miss", "pad": int(n["pad"]), "index": i, "seq": int(n["seq"]), "time": resolved_at[i]})


func _seq_at(t: float) -> int:
	for s in sequences:
		if t >= float(s["start_time"]) - accept_s and t < float(s["end_time"]):
			return int(s["index"])
	return -1
