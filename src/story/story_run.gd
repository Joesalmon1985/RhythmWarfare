class_name StoryRun
extends RefCounted
## One play-through of a story chapter with no nodes, advanced by song time: the existing Match (pad recognition, the two-bar
## sequence tracker, stem mute events) in rhythm-only mode, the crowd energy model and the director. StoryPlay drives it from the
## song clock; tests drive it headless at any frame step. Judgement is untouched: Match.setup(level, null, false).

var data: StoryData
var level: Level
var match_ref: Match
var crowd := CrowdController.new()
var director := StoryDirector.new()
var errors: Array = []
var warnings: Array = []
var finished := false  # the song reached its end and every sequence is final
var song_ended := false
var judge_counts := {"perfect": 0, "great": 0, "good": 0, "ok": 0, "miss": 0, "stray": 0}


## Loads the chapter, its music pack and the level through the normal loader. `options` is the LevelLoader's
## ("loadout", "library", "unlocked"); defaults resolve like a campaign mission with the global loadout.
static func create(options: Dictionary = {}, data_path: String = StoryData.PATH) -> StoryRun:
	var run := StoryRun.new()
	var loaded := StoryData.load_file(data_path)
	run.errors.append_array(loaded["errors"])
	if loaded["data"] == null:
		return run
	run.data = loaded["data"]
	var lr := LevelLoader.load_pack(str(run.data.raw["music_pack"]), options)
	run.errors.append_array(lr["errors"])
	run.warnings.append_array(lr["warnings"])
	if lr["level"] == null:
		return run
	run.level = lr["level"]
	if run.level.sequence_bars != run.data.sequence_bars:
		run.errors.append("level sequences are %d bars, the chapter expects %d" % [run.level.sequence_bars, run.data.sequence_bars])
	if run.level.bar_count() != run.data.duration_bars:
		run.errors.append("level has %d bars, the chapter expects %d" % [run.level.bar_count(), run.data.duration_bars])
	run.reset()
	run.warnings.append_array(run.director.warnings)
	return run


func reset() -> void:
	match_ref = Match.new()
	match_ref.setup(level, null, false)
	crowd.setup(data)
	director.setup(data, level, crowd)
	finished = false
	song_ended = false
	judge_counts = {"perfect": 0, "great": 0, "good": 0, "ok": 0, "miss": 0, "stray": 0}


## Advance to song time `t`. Returns {judge: [...], events: [...] (stem/program for the transport), actions: [...] (director)}.
func step(t: float) -> Dictionary:
	var judge_events := match_ref.advance(t)
	for ev in judge_events:
		var k := str(ev["kind"])
		if k == "hold_fail":
			k = "miss"
		if judge_counts.has(k):
			judge_counts[k] += 1
	var events := match_ref.drain_events()
	for ev in events:
		if ev["kind"] == "sequence":
			crowd.apply(ev["result"])
	var actions := director.update(t)
	if t >= level.duration_seconds() and not song_ended:
		song_ended = true
	if song_ended and not finished:
		var late := _flush()
		events.append_array(late["events"])
		actions.append_array(late["actions"])
	return {"judge": judge_events, "events": events, "actions": actions}


## After the song's last bar: let the final cue windows elapse, resolve the remaining sequences exactly like any other.
func _flush() -> Dictionary:
	var events: Array = []
	var actions: Array = []
	if crowd.history.size() < level.sequences.size():
		match_ref.pad_judge.update(level.duration_seconds() + 1.0)
		for r in match_ref.tracker.update():
			crowd.apply(r)
			events.append({"kind": "sequence", "result": r})
		actions = director.update(level.duration_seconds() + 1.0)
	if crowd.history.size() >= level.sequences.size():
		finished = true
	return {"events": events, "actions": actions}


func total_sequences() -> int:
	return level.sequences.size()


func ending() -> String:
	return director.ending() if director.ending() != "" else crowd.ending(total_sequences())


## The summary the result screen and the save use.
func summary() -> Dictionary:
	var pj := match_ref.pad_judge
	var branches: Array = []
	for d in crowd.decisions_log:
		branches.append({"id": d["id"], "title": d["title"], "outcome": d["outcome"], "text": d["text"], "bar": d["bar"]})
	var energy_curve: Array = []
	for h in crowd.history:
		energy_curve.append(snappedf(float(h["energy"]), 0.1))
	return {"ending": ending(), "ending_rank": data.ending_rank(ending()), "energy": snappedf(crowd.energy, 0.1), "sequences_passed": crowd.passed_count(), "sequences_total": total_sequences(),
		"accuracy": pj.accuracy(), "best_combo": pj.best_combo, "perfect": pj.perfect, "great": pj.great, "ok": pj.ok, "misses": pj.misses,
		"strays": pj.strays, "branches": branches, "energy_curve": energy_curve, "peak_energy": snappedf(_peak(), 0.1)}


func _peak() -> float:
	var p := crowd.data.initial_energy
	for h in crowd.history:
		p = maxf(p, float(h["energy"]))
	return p


## Headless driver for tests and tuning: plays the whole song with a seeded input policy (tools/autoplay.gd) at a given frame
## step (0 = a variable step pattern) and returns the summary plus the director log.
static func autoplay(policy: String, frame_s: float = 1.0 / 60.0, seed_value: int = 1, options: Dictionary = {}, data_path: String = StoryData.PATH) -> Dictionary:
	var run := StoryRun.create(options, data_path)
	if not run.errors.is_empty():
		return {"errors": run.errors}
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var harness: Script = load("res://tools/autoplay.gd")
	var plan: Array = harness.plan_inputs(run.level, policy, rng)
	var k := 0
	var down := {}
	var t := -0.5
	var step_i := 0
	var duration := run.level.duration_seconds()
	var vary := [0.004, 0.031, 0.016, 0.05, 0.009, 0.022]
	while not run.finished and t < duration + 2.0:
		t += frame_s if frame_s > 0.0 else vary[step_i % vary.size()]
		step_i += 1
		while k < plan.size() and float(plan[k]["t"]) <= t:
			var e: Dictionary = plan[k]
			if e["down"]:
				if down.has(e["pad"]):
					run.match_ref.release(int(e["pad"]), float(e["t"]), int(e["pad"]))
				down[e["pad"]] = e["id"]
				run.match_ref.press(int(e["pad"]), float(e["t"]), int(e["pad"]))
			elif down.get(e["pad"], null) == e["id"]:
				down.erase(e["pad"])
				run.match_ref.release(int(e["pad"]), float(e["t"]), int(e["pad"]))
			k += 1
		run.step(t)
	var s := run.summary()
	s["log"] = run.director.fired
	s["run"] = run
	return s
