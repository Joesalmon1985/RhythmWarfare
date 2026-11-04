class_name CrowdController
extends RefCounted
## The crowd energy model: one update per resolved two-bar sequence (the existing SequenceTracker result, exactly once),
## 0..100, reversible. Also the deterministic rules for the authored decisions and the endings. Pure, no nodes.

var data: StoryData
var energy := 45.0
var history: Array = []  # per resolved sequence: {index, passed, grade, energy, delta, resolve_time}
var decisions_log: Array = []  # [{id, outcome, bar, energy, recent_pass, fired_t}]
var _seen := {}


func setup(p_data: StoryData) -> void:
	data = p_data
	energy = data.initial_energy
	history = []
	decisions_log = []
	_seen = {}


## Applies a sequence result once. Returns the delta (0 for a duplicate).
func apply(result: Dictionary) -> float:
	var idx := int(result["index"])
	if _seen.has(idx):
		return 0.0
	_seen[idx] = true
	var cfg: Dictionary = data.energy_cfg
	var delta := float(cfg["fail_delta"])
	if result["passed"]:
		delta = float(cfg["pass_delta"].get(str(result["grade"]), 2))
	energy = clampf(energy + delta, float(cfg["min"]), float(cfg["max"]))
	history.append({"index": idx, "passed": bool(result["passed"]), "grade": str(result["grade"]), "energy": energy, "delta": delta,
		"resolve_time": float(result.get("resolve_time", 0.0))})
	return delta


func band() -> String:
	return data.band_of(energy)


func passed_count() -> int:
	var n := 0
	for h in history:
		if h["passed"]:
			n += 1
	return n


func pass_rate_all(total: int) -> float:
	return float(passed_count()) / float(maxi(total, 1))


## Pass rate over the last `n` resolved sequences up to and including list position `upto` (exclusive end).
func recent_pass(n: int, upto: int = -1) -> float:
	var end := history.size() if upto < 0 else mini(upto, history.size())
	var start := maxi(end - n, 0)
	if end == start:
		return 0.0
	var p := 0
	for i in range(start, end):
		if history[i]["passed"]:
			p += 1
	return float(p) / float(end - start)


## Mean of the energy after each of the last `n` sequences before position `upto` (smooths a single swing).
func smooth_energy(n: int, upto: int = -1) -> float:
	var end := history.size() if upto < 0 else mini(upto, history.size())
	var start := maxi(end - n, 0)
	if end == start:
		return energy
	var s := 0.0
	for i in range(start, end):
		s += float(history[i]["energy"])
	return s / float(end - start)


## Decides one authored branch from the first `upto` resolved sequences (those ending before the decision bar).
## Rule: smoothed energy against energy_min with a dead band (inside it the previous branch is kept, so one sequence
## cannot flip it), and the recent pass rate must reach recent_pass_min. A "winback" decision is good only after an earlier
## bad outcome and a strong recent run. Returns {outcome: "good"|"bad", ...explanation}.
func decide(d: Dictionary, upto: int) -> Dictionary:
	var rule: Dictionary = d["rule"]
	var recent := recent_pass(int(rule.get("recent_sequences", 8)), upto)
	var smooth := smooth_energy(int(rule.get("smooth", 4)), upto)
	var last_outcome := ""
	var had_bad := false
	for l in decisions_log:
		if l.get("kind", "") != "winback":
			last_outcome = str(l["outcome"])
			had_bad = had_bad or l["outcome"] == "bad"
	var outcome := "bad"
	if d.get("kind", "") == "winback":
		outcome = "good" if (had_bad and recent >= float(rule["recent_pass_min"]) and smooth >= float(rule["energy_min"])) else "bad"
	else:
		var emin := float(rule["energy_min"])
		var band := float(rule.get("dead_band", 0.0))
		var pass_ok := recent >= float(rule["recent_pass_min"])
		if not pass_ok:
			outcome = "bad"
		elif smooth >= emin + band:
			outcome = "good"
		elif smooth < emin - band:
			outcome = "bad"
		else:
			outcome = last_outcome if not last_outcome.is_empty() else "good"
	return {"id": str(d["id"]), "outcome": outcome, "energy": smooth, "recent_pass": recent, "kind": str(d.get("kind", "")),
		"sequences": upto}


## The ending from the closing energy and the overall pass rate over `total` sequences (first match in ending_order).
func ending(total: int) -> String:
	var rate := pass_rate_all(total)
	for key in data.ending_order:
		var e: Dictionary = data.endings[key]
		if energy >= float(e["energy_min"]) and rate >= float(e["pass_min"]):
			return str(key)
	return str(data.ending_order[data.ending_order.size() - 1])


## A projection of the ending from the sequences resolved so far (for the closing lean); `total` is the song's sequence count.
func ending_lean() -> String:
	return ending(maxi(history.size(), 1))


## The energy as it stood at song time `t`: only the results that were final by then count, so a decision made at `t`
## cannot depend on when a later result happened to reach the frame loop.
func energy_at(t: float) -> float:
	var e := data.initial_energy
	for h in history:
		if float(h["resolve_time"]) > t:
			break
		e = float(h["energy"])
	return e


func ending_lean_at(t: float) -> String:
	var n := 0
	var p := 0
	var e := data.initial_energy
	for h in history:
		if float(h["resolve_time"]) > t:
			break
		n += 1
		e = float(h["energy"])
		if h["passed"]:
			p += 1
	var rate := float(p) / float(maxi(n, 1))
	for key in data.ending_order:
		var en: Dictionary = data.endings[key]
		if e >= float(en["energy_min"]) and rate >= float(en["pass_min"]):
			return str(key)
	return str(data.ending_order[data.ending_order.size() - 1])
