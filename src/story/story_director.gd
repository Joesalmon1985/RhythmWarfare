class_name StoryDirector
extends RefCounted
## Schedules the chapter's authored visual actions against the song's exact ticks (never frame counts or accumulated delta) and
## owns the branch decisions. update(t) takes the song time and returns the actions that became due since the last call; it is
## a pure function of (t, resolved sequence results), so any frame step yields the same actions with the same `t0`.
##
## A decision at bar B needs every two-bar sequence that ends at or before B to be final. If the song clock reaches B first the
## decision is held pending (the clock never waits) and fires with t0 = max(B's time, the last required result's resolve time).
## Guards (`when`) are evaluated on the energy as of the event's own time, so late-arriving later results cannot change them.

var data: StoryData
var level: Level
var crowd: CrowdController
var fired: Array = []  # every emitted action: {t0, bar, action, args, block, source}

var _timeline: Array = []  # {t, bar, kind: "event"|"decision"|"lean", e/d}
var _cursor := 0
var _pending: Array = []  # decisions whose time came but whose sequences are not all final
var _total_sequences := 0
var _ending := ""
var _ending_fired := false


func setup(p_data: StoryData, p_level: Level, p_crowd: CrowdController) -> void:
	data = p_data
	level = p_level
	crowd = p_crowd
	fired = []
	_timeline = []
	_cursor = 0
	_pending = []
	_ending = ""
	_ending_fired = false
	_total_sequences = level.sequences.size()
	var order := 0
	for b in data.blocks:
		for e in b["events"]:
			_timeline.append({"t": bar_time(float(e["at_bar"])), "order": order, "kind": "event", "e": e, "bar": float(e["at_bar"]), "block": str(b["id"])})
			order += 1
	for d in data.decisions:
		_timeline.append({"t": bar_time(float(d["at_bar"])), "order": order, "kind": "decision", "d": d, "bar": float(d["at_bar"]), "block": str(d.get("block", ""))})
		order += 1
	_timeline.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["order"] < b["order"] if is_equal_approx(a["t"], b["t"]) else a["t"] < b["t"])


func bar_time(bar: float) -> float:
	return level.tick_to_seconds(int(round((bar - 1.0) * float(level.ticks_per_bar()))))


## Sequences that must be final before the decision at `bar` (those ending at or before it).
func required_sequences(bar: float) -> int:
	var tick := int(round((bar - 1.0) * float(level.ticks_per_bar())))
	var n := 0
	for s in level.sequences:
		if int(s["end_tick"]) <= tick:
			n += 1
	return n


func update(t: float) -> Array:
	var out: Array = []
	while _cursor < _timeline.size() and float(_timeline[_cursor]["t"]) <= t:
		var item: Dictionary = _timeline[_cursor]
		_cursor += 1
		match item["kind"]:
			"event":
				_fire_event(item, out)
			"decision":
				_pending.append(item)
	var still: Array = []
	for item in _pending:
		var d: Dictionary = item["d"]
		var need := required_sequences(float(d["at_bar"]))
		if crowd.history.size() < need:
			still.append(item)
			continue
		var res := crowd.decide(d, need)
		var t0 := float(item["t"])
		if need > 0:
			t0 = maxf(t0, float(crowd.history[need - 1]["resolve_time"]))
		res["fired_t"] = t0
		res["bar"] = float(d["at_bar"])
		res["title"] = str(d["title"])
		res["text"] = str(d.get("good_text" if res["outcome"] == "good" else "bad_text", ""))
		crowd.decisions_log.append(res)
		for a in d.get(res["outcome"], []):
			var args := {"decision": str(d["id"]), "outcome": res["outcome"]}
			var name := str(a)
			if typeof(a) == TYPE_DICTIONARY:
				name = str(a["action"])
				for k in a:
					if k != "action":
						args[k] = a[k]
			_emit(out, t0, float(d["at_bar"]), name, args, str(item["block"]), "decision")
	_pending = still
	if not _ending_fired and _total_sequences > 0 and crowd.history.size() >= _total_sequences:
		_ending_fired = true
		_ending = crowd.ending(_total_sequences)
		var last_t := float(crowd.history[_total_sequences - 1]["resolve_time"])
		_emit(out, maxf(last_t, bar_time(float(data.duration_bars) + 1.0)), float(data.duration_bars) + 1.0, "ending", {"ending": _ending}, "closing_tableau", "ending")
	return out


func _fire_event(item: Dictionary, out: Array) -> void:
	var e: Dictionary = item["e"]
	var t: float = item["t"]
	var action := str(e["action"])
	var args := e.duplicate()
	args.erase("at_bar")
	args.erase("action")
	if e.has("when"):
		if not _guard_ok(e["when"], t):
			if e.has("else"):
				action = str(e["else"])
				args["alternative"] = true
			else:
				return
	if action == "ending_lean":
		args["ending"] = crowd.ending_lean_at(t)
	_emit(out, t, float(item["bar"]), action, args, str(item["block"]), "block")


func _guard_ok(w: Dictionary, t: float) -> bool:
	var e := crowd.energy_at(t)
	if w.has("energy_min") and e < float(w["energy_min"]):
		return false
	if w.has("energy_max") and e > float(w["energy_max"]):
		return false
	return true


func _emit(out: Array, t0: float, bar: float, action: String, args: Dictionary, block: String, source: String) -> void:
	var a := {"t0": t0, "bar": bar, "action": action, "args": args, "block": block, "source": source}
	fired.append(a)
	out.append(a)


## Blocks that fired at least one action (for coverage checks).
func blocks_with_actions() -> Dictionary:
	var out := {}
	for a in fired:
		out[str(a["block"])] = int(out.get(str(a["block"]), 0)) + 1
	return out


func ending() -> String:
	return _ending
