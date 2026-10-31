class_name SequenceTracker
extends RefCounted
## Turns resolved cues into sequence results (PRD section 15). A sequence resolves once every one of its cues is final,
## at the latest of their resolution times (so never before a future cue was judged, and identically at any frame
## rate). Success: credit / cues >= the mission's threshold. Precision (only for a success) = mean absolute onset error
## of its accepted cues plus a stray penalty, graded sharp / steady / loose, which sets the construction delay.
## Each sequence resolves exactly once; a failure earns nothing and the next sequence starts normally.

var level: Level
var judge: PadJudge
var results: Array = []  # per sequence index: {} until resolved
var _cues_of: Dictionary = {}  # sequence index -> Array[int] cue indexes
var _next := 0  # sequences resolve in order


func setup(p_level: Level, p_judge: PadJudge) -> void:
	level = p_level
	judge = p_judge
	results = []
	_cues_of = {}
	_next = 0
	for s in level.sequences:
		results.append({})
		_cues_of[int(s["index"])] = []
	for i in level.notes.size():
		var si := int(level.notes[i]["seq"])
		if _cues_of.has(si):
			_cues_of[si].append(i)


## Returns the sequences that resolved since the last call, in order.
func update() -> Array:
	var out: Array = []
	while _next < level.sequences.size():
		var s: Dictionary = level.sequences[_next]
		var idx: Array = _cues_of[int(s["index"])]
		var done := true
		var at := float(s["start_time"])
		for i in idx:
			if not judge.is_resolved(i):
				done = false
				break
			at = maxf(at, judge.resolved_at[i])
		if not done:
			break
		var total := 0.0
		var abs_sum := 0.0
		var hits := 0
		for i in idx:
			total += judge.credit[i]
			if not is_nan(judge.delta_ms[i]):
				abs_sum += absf(judge.delta_ms[i])
				hits += 1
		var ratio := total / float(maxi(idx.size(), 1))
		var strays := int(judge.strays_by_seq.get(int(s["index"]), 0))
		var mean_ms := abs_sum / float(hits) if hits > 0 else 999.0
		var passed := ratio + 0.0001 >= level.sequence_threshold
		var r := {"index": int(s["index"]), "passed": passed, "credit": ratio, "cues": idx.size(), "accepted": hits,
			"mean_abs_ms": mean_ms, "strays": strays, "resolve_time": at, "reward": str(s["reward"]), "mode": str(s["mode"])}
		r["grade"] = MissionRules.grade(mean_ms, strays, idx.size()) if passed else ""
		r["delay_s"] = MissionRules.delay_s(r["grade"]) if passed else 0.0
		results[_next] = r
		out.append(r)
		_next += 1
	return out


## Progress of the sequence that contains song time t: {index, cues, resolved, credit, total} or {}.
func progress_at(t: float) -> Dictionary:
	for s in level.sequences:
		if t >= float(s["start_time"]) and t < float(s["end_time"]):
			var idx: Array = _cues_of[int(s["index"])]
			var resolved := 0
			var got := 0.0
			for i in idx:
				if judge.is_resolved(i):
					resolved += 1
					got += judge.credit[i]
			return {"index": int(s["index"]), "cues": idx.size(), "resolved": resolved, "credit": got, "reward": str(s["reward"]),
				"start_time": float(s["start_time"]), "end_time": float(s["end_time"])}
	return {}


func passed_count() -> int:
	var n := 0
	for r in results:
		if not r.is_empty() and r["passed"]:
			n += 1
	return n


func grade_counts() -> Dictionary:
	var out := {"sharp": 0, "steady": 0, "loose": 0, "failed": 0}
	for r in results:
		if r.is_empty():
			continue
		if r["passed"]:
			out[r["grade"]] += 1
		else:
			out["failed"] += 1
	return out
