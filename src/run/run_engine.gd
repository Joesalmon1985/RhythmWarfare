class_name RunEngine
extends RefCounted
## The continuous run as pure logic (no nodes, no audio, no clock of its own): it is advanced with song time and answers with events.
##
## A phase is 64 beats at 174 BPM: four blocks of 16. Block b of a phase plays the cue family of the current mix stage (drums alone,
## bass enters, drums return, bass strongest). At each block's decision beat the block is judged: a pass moves the stage one step on, a
## miss holds the stage (and so the cue family) for the next block. The phase length never changes; the last block carries the
## direction choice. Cues are appended to `level.notes` one block ahead (the judge, pad view and note lane read the growing list), and
## the first block of the next phase is charted at the last block's decision from the selected route (the default, or the player's pick), and the chart is then locked: a route
## whose scene charts another pack can no longer be chosen. A scene is one phase at a place in a world; a world is a small graph of scenes (RunData).
##
## Everything is a function of (song time, the judge's results, the player's choice), so any frame step, a pause or a calibration change
## gives the same events at the same song times.

const TICKS := 960
const GUARD_NOTE := "cue_free_guard"

var data: RunData
var cfg: Dictionary
var level: Level
var judge := PadJudge.new()
var beat_s := 60.0 / 174.0

var energy := 60.0
var over := false  # the run has ended (depleted); the scene shows the game-over screen
var node_id := ""
var depth := 1
var phase_n := 0  # phases entered so far in this run, counting the current one (1 for the first)
var phase_t0 := 0.0  # song time of the current phase's downbeat
var stage := 0  # mix stage in force for the current block
var block := 0  # block being played (0..3)
var bass_origin := -1  # phase beat the bass and synth started from (-1: not revealed yet)
var stage_of_block: Array = []
var block_credit: Array = []
var choice := ""  # the chosen destination node id ("" until the player picks one)
var window_open := false
var hotspots: RunHotspots = null  # when set, the route is the outcome of a hotspot (the tap is the intent, block 4 decides): see _hotspot_decision; null keeps the plain route choice (tests, RW_RUN_ARROWS=1)
var hold := false  # a minigame owns the scene (MinigameController): the run stays here, no hotspot commits, the chart and the route lock agree on this node; phases, cues, judging and energy go on as usual
var route_locked := false  # block 0 of the next phase has been charted: routes with another chart pack can no longer be chosen
var _locked_chart := ""

var _events: Array = []
var _next_block_notes := {}  # block index -> true once charted
var _next_phase_charted := false
var _depleted_t := -1.0
var _over_t := -1.0
var _blocks_total := 0  # blocks charted in this run (for sequence ids)
var _note_id := 0
var part_offset := {"drums": 0.0, "bass": 0.0}  # seconds the audible part sits from the grid in the current phase (RunAudio measures it)


func _init(p_data: RunData = null) -> void:
	if p_data != null:
		setup(p_data)


func setup(p_data: RunData) -> void:
	data = p_data
	cfg = data.cfg
	beat_s = 60.0 / float(cfg["timing"]["bpm"])


func timing(key: String) -> float:
	return float(cfg["timing"][key])


func phase_s() -> float:
	return timing("phase_beats") * beat_s


## Starts a run at `start_id` with fresh energy. Song time 0 is the first downbeat.
func begin(start_id: String) -> void:
	level = Level.new()
	level.mode = "defense"
	level.bpm = float(cfg["timing"]["bpm"])
	level.ticks_per_beat = TICKS
	level.beats_per_bar = 4
	level.title = "Continuous run"
	level.sequence_threshold = float(cfg["judgement"]["pass_credit"])
	judge = PadJudge.new()
	var w: Dictionary = cfg["judgement"]["windows_ms"]  # the run's own windows: nothing is read from the old campaign rules
	judge.perfect_s = float(w["perfect"]) / 1000.0
	judge.great_s = float(w["great"]) / 1000.0
	judge.accept_s = float(w["accept"]) / 1000.0
	judge.complete_s = float(cfg["judgement"]["hold_complete_s"])
	judge.setup(level.notes, [])
	energy = float(cfg["energy"]["start"])
	over = false
	_events = []
	_depleted_t = -1.0
	_over_t = -1.0
	_blocks_total = 0
	_note_id = 0
	phase_n = 0
	phase_t0 = 0.0
	_next_phase_charted = false
	_enter(start_id, 0.0, true)


## Starts again after an excursion (the Bassment): the song clock has run on, so the new phase begins at song time `t0` (a downbeat); a fresh level and judge, the
## crowd's energy kept, the phase count carried on. The cues and ticks are absolute, so nothing but `phase_t0` knows the run was away.
func resume(start_id: String, t0: float) -> void:
	var keep := energy
	var n := phase_n
	level = Level.new()
	level.mode = "defense"
	level.bpm = float(cfg["timing"]["bpm"])
	level.ticks_per_beat = TICKS
	level.beats_per_bar = 4
	level.title = "Continuous run"
	level.sequence_threshold = float(cfg["judgement"]["pass_credit"])
	judge = PadJudge.new()
	var w: Dictionary = cfg["judgement"]["windows_ms"]
	judge.perfect_s = float(w["perfect"]) / 1000.0
	judge.great_s = float(w["great"]) / 1000.0
	judge.accept_s = float(w["accept"]) / 1000.0
	judge.complete_s = float(cfg["judgement"]["hold_complete_s"])
	judge.setup(level.notes, [])
	energy = keep
	over = false
	_events = []
	_depleted_t = -1.0
	_over_t = -1.0
	_next_phase_charted = false
	phase_n = n
	_enter(start_id, t0, true)


func _enter(id: String, t0: float, chart_now: bool) -> void:
	var prev := node_id if phase_n > 0 else ""
	node_id = id
	var n: Dictionary = data.nodes[id]
	depth = int(n["depth"])
	phase_n += 1
	phase_t0 = t0
	stage = 0
	block = 0
	bass_origin = -1
	choice = ""
	window_open = false
	route_locked = false
	_locked_chart = ""
	stage_of_block = [0]
	block_credit = []
	_next_block_notes = {}
	part_offset = {"drums": 0.0, "bass": 0.0}
	if chart_now or not _next_phase_charted:
		_chart_block(0, 0, depth)
	_next_phase_charted = false
	_next_block_notes[0] = true
	if hotspots != null:
		hotspots.begin_scene(id, energy)
	_emit({"kind": "phase_start", "node": id, "world": n["world"], "scene": n["scene"], "from": prev, "depth": depth, "t": t0, "phase": phase_n, "treatment": n["treatment"],
		"audio": n["audio"], "temporary": n["temporary"], "fresh": phase_n == 1})
	_emit({"kind": "mix", "stage": 0, "t": t0, "gains": cfg["stages"][0]["gains"], "cue": cfg["stages"][0]["cue"]})


func _emit(ev: Dictionary) -> void:
	_events.append(ev)


## Song time of a beat of the current phase.
func t_of(phase_beat: float) -> float:
	return phase_t0 + phase_beat * beat_s


## The beat of a block at which it is judged (and a hotspot commits).
func _decision_beat() -> float:
	return maxf(timing("decision_beat"), timing("cue_span_beats") + judge.accept_s / beat_s + 0.05)


## The routes out of the current scene: [{to, dir, label, default, in_world, title}]: the paths inside the world, or at the exit scene the other worlds.
func options() -> Array:
	var out: Array = []
	var first := true
	for e in data.nodes[node_id]["next"]:
		var o: Dictionary = (e as Dictionary).duplicate()
		o["default"] = first
		o["in_world"] = str(data.nodes[str(e["to"])]["world"]) == str(data.nodes[node_id]["world"])
		o["title"] = data.route_title(node_id, str(e["to"]))
		first = false
		out.append(o)
	return out


func default_route() -> String:
	return str(data.nodes[node_id]["next"][0]["to"])


## The player picks a route (by destination id); allowed until the phase ends. Returns false when the id is not one of the routes.
func choose(to: String) -> bool:
	if hotspots != null:  # with hotspots the route is the outcome of the selected one: choosing a route taps the hotspot that leads there (scripted play, old callers)
		return hotspots.select_route(to, block, window_open)
	for e in data.nodes[node_id]["next"]:
		if str(e["to"]) == to:
			if not route_allowed(to):
				return false
			choice = to
			return true
	return false


func choose_dir(dir: String) -> bool:
	for e in data.nodes[node_id]["next"]:
		if str(e["dir"]) == dir:
			return choose(str(e["to"]))
	return false


## False for a route whose chart pack differs from the one already charted for the next phase's first block (the lock falls at the last block's decision, beat 60.5).
func route_allowed(to: String) -> bool:
	return not route_locked or str(data.nodes[to]["chart"]) == _locked_chart


func selected_route() -> String:
	if hold:
		return node_id
	if choice != "":
		return choice
	if hotspots != null and hotspots.selected != "":  # the route the selected hotspot leads to on success (the final outcome is only known at the commit)
		var r := str((hotspots.get_hotspot(hotspots.selected).get("on_success", {}) as Dictionary).get("route", ""))
		if r != "" and not HotspotContract.is_trial_route(r):
			return r
	return default_route()


func press(pad: int, t: float, touch: int = 0) -> Dictionary:
	return judge.press(pad, t, touch)


func release(pad: int, t: float, touch: int = 0) -> Dictionary:
	return judge.release(pad, t, touch)


## The family cued in block `b` of the current phase.
func cue_family(b: int) -> String:
	return str(cfg["stages"][int(stage_of_block[mini(b, stage_of_block.size() - 1)])]["cue"])


## Advance to song time `t`; returns the events that became due, in order.
func update(t: float) -> Array:
	if level == null:
		return []
	judge.update(t)
	for ev in judge.drain_events():
		_emit({"kind": "judge", "event": ev, "t": t})
	if _depleted_t >= 0.0:
		if not over and t >= _over_t:
			over = true
			_emit({"kind": "run_over", "t": _over_t, "energy": energy, "phase": phase_n, "node": node_id})
	else:
		var bb := int(timing("block_beats"))
		var guard := 0
		while block <= 3 and guard < 8 and t >= t_of(float(block * bb) + _decision_beat()):
			guard += 1
			_decide(block, t_of(float(block * bb) + _decision_beat()))
			if _depleted_t >= 0.0:
				break
		if _depleted_t < 0.0 and block == 4 and t >= t_of(timing("phase_beats")):
			_commit()
			var first := _events
			_events = []
			first.append_array(update(t))
			return first
	var out := _events
	_events = []
	return out


func _commit() -> void:
	var to := selected_route()
	var t0 := t_of(timing("phase_beats"))
	_emit({"kind": "route_commit", "from": node_id, "to": to, "chosen": choice != "", "t": t0, "treatment": data.nodes[to]["treatment"],
		"same_world": str(data.nodes[to]["world"]) == str(data.nodes[node_id]["world"])})
	window_open = false
	_enter(to, t0, false)


## Judge block `b` at its decision beat, update the mix stage and energy, chart what comes next.
func _decide(b: int, t_dec: float) -> void:
	judge.update(t_dec)
	var credit := block_credit_of(b)
	var passed := credit >= float(cfg["judgement"]["pass_credit"])
	block_credit.append(credit)
	var e: Dictionary = cfg["energy"]
	var pc := float(cfg["judgement"]["pass_credit"])
	if passed:
		energy += float(e["pass_gain"]) + float(e["pass_bonus"]) * (credit - pc) / maxf(1.0 - pc, 0.001)
	else:
		energy -= float(e["fail_loss"]) * (pc - credit) / pc + 3.0
	energy = clampf(energy, 0.0, float(e["max"]))
	var boundary_beat := float((b + 1) * int(timing("block_beats")))
	var next_stage := stage
	if b < 3 and passed:
		next_stage = mini(stage + 1, 3)
	_emit({"kind": "block_result", "block": b, "credit": credit, "passed": passed, "energy": energy, "stage": stage, "next_stage": next_stage, "t": t_dec,
		"node": node_id, "phase": phase_n})
	block = b + 1
	if hotspots != null and energy > 0.0 and not hold:
		_hotspot_decision(b, passed, t_dec, credit)
	if energy <= 0.0:
		_depleted_t = t_of(boundary_beat)
		_over_t = _depleted_t + float(cfg["timing"]["fade_beats"]) * beat_s
		_emit({"kind": "depleted", "t": _depleted_t, "fade_s": _over_t - _depleted_t, "node": node_id})
		return
	if b < 3:
		stage = next_stage
		stage_of_block.append(stage)
		var st: Dictionary = cfg["stages"][stage]
		if stage >= 1 and bass_origin < 0:
			bass_origin = int(boundary_beat)
			_emit({"kind": "reveal", "beat": bass_origin, "t": t_of(boundary_beat), "node": node_id, "block": b + 1})
		_emit({"kind": "mix", "stage": stage, "t": t_of(boundary_beat), "gains": st["gains"], "cue": st["cue"], "beat": boundary_beat})
		_chart_block(b + 1, b + 1, depth)
		_next_block_notes[b + 1] = true
		if b == 2:  # the choice window is the last block: riser when the final bass stage is reached by beat 49, a fall otherwise
			window_open = true
			_emit({"kind": "route_window", "t": t_of(boundary_beat), "effect": "riser" if stage == 3 else "fall", "options": options(),
				"default": default_route(), "stage": stage})
	else:
		# the last block is over: chart the next phase's first block now from the selected route, and lock it
		if hold:
			choice = node_id
		_chart_next_phase()


## The hotspot window's decisions at the block's decision beat (inside the cue-free guard): the early window (a way into the Bassment) commits at blocks 0 and 1, the final one at block 3 (the route
## lock beat), where the outcome's route becomes the engine's choice before the next phase is charted from it. The outcome's energy is applied here (never to the point of depletion).
func _hotspot_decision(b: int, passed: bool, t_dec: float, credit := -1.0) -> void:
	hotspots.energy = energy
	var out: Dictionary = {}
	if b <= 2:
		out = hotspots.on_block(b, passed, credit)
	else:
		out = hotspots.commit_final(passed, credit)
		if not out.is_empty():
			choice = str(out["route"])
	if out.is_empty():
		return
	if float(out["energy"]) != 0.0:
		energy = clampf(energy + float(out["energy"]), 1.0, float(cfg["energy"]["max"]))
		hotspots.energy = energy
	_emit({"kind": "hotspot_commit", "t": t_dec, "block": b, "node": node_id, "phase": phase_n, "outcome": out, "energy": energy})


func _chart_next_phase() -> void:
	var to := selected_route()  # the player's pick so far, else the default: the chosen world's own chart, then locked
	_chart_block(0, 0, int(data.nodes[to]["depth"]), to, true)
	_next_phase_charted = true
	route_locked = true
	_locked_chart = str(data.nodes[to]["chart"])


## Credit of block `b` of the current phase: the mean credit of its cues (1 when it has none).
func block_credit_of(b: int) -> float:
	var sum := 0.0
	var n := 0
	for i in level.notes.size():
		var note: Dictionary = level.notes[i]
		if int(note["phase"]) == phase_n and int(note["block"]) == b:
			n += 1
			sum += judge.credit[i] if judge.is_resolved(i) else 0.0
	return 1.0 if n == 0 else sum / float(n)


## Appends the cues of block `b` (stage `stage_i` of the phase) to the level and the judge.
func _chart_block(b: int, stage_i: int, at_depth: int, node_for_chart: String = "", next_phase := false) -> void:
	var nid := node_for_chart if node_for_chart != "" else node_id
	var st_idx := int(stage_of_block[stage_i]) if stage_i < stage_of_block.size() and not next_phase else 0
	var fam := str(cfg["stages"][st_idx]["cue"])
	var block_beats := int(timing("block_beats"))
	var start_beat := b * block_beats
	var pack: Dictionary = data.packs[data.chart_pack_at(nid, start_beat)]  # the pack of the section playing at this block (the scene's chart pack when it has no arrangement)
	var tier := str(data.tier_of(at_depth))
	var cues: Array = pack["tiers"][tier]["drums" if fam == "drums" else "bass"]
	var phrase_beats := int(pack["phrase_beats"])
	var origin := 0 if fam == "drums" or next_phase else maxi(bass_origin, 0)
	origin = maxi(origin, data.section_start_at(nid, start_beat))  # a new section's loops start with the section, so its phrase does too
	var pos := ((start_beat - origin) % phrase_beats + phrase_beats) % phrase_beats  # phrase beat the block starts at
	var span := timing("cue_span_beats")
	var tpb := level.ticks_per_beat
	var phase_n_for := phase_n + 1 if next_phase else phase_n
	var phase_beat0 := phase_n_for_first_beat(phase_n_for)
	var added: Array = []
	for c in cues:
		var off: int = int(c[0]) - pos * tpb
		if off < 0 or off >= block_beats * tpb:
			continue
		var beat_in_block := float(off) / float(tpb)
		if beat_in_block > span + 1e-6:
			continue
		var dur: int = int(c[1])
		if dur > 0:
			dur = mini(dur, int(round((span - beat_in_block) * tpb)))
			if dur < 480:
				dur = 0
		var gbeat := phase_beat0 + start_beat + off / float(tpb)
		var tick := int(round(gbeat * tpb))
		var tm := float(tick) * 60.0 / (level.bpm * float(tpb)) + (float(part_offset["drums"]) if fam == "drums" else float(part_offset["bass"])) * (0.0 if next_phase else 1.0)
		var fam_c := str(c[3]) if c.size() > 3 else fam
		added.append({"id": "r%05d" % _note_id, "tick": tick, "duration_ticks": dur, "end_tick": tick + dur, "time": tm, "end_time": tm + float(dur) * 60.0 / (level.bpm * float(tpb)),
			"pad": int(c[2]), "button": int(c[2]), "family": fam_c, "lane": fam_c, "slot_id": fam_c, "type": "hold" if dur > 0 else "tap", "seq": _blocks_total,
			"phase": phase_n_for, "block": b, "voice": fam})
		_note_id += 1
	added.sort_custom(func(x: Dictionary, y: Dictionary) -> bool: return x["tick"] < y["tick"] if x["tick"] != y["tick"] else x["pad"] < y["pad"])
	for a in added:
		level.notes.append(a)
	var block_start_tick := int(round((phase_beat0 + start_beat) * tpb))
	var pads := {}
	if fam == "drums":
		pads = {"1": {"family": "kick", "ref": ""}, "4": {"family": "snare", "ref": ""}}
	else:
		for p in range(1, 5):
			pads[str(p)] = {"family": "bass", "ref": ""}
	level.sections.append({"id": "p%d_b%d" % [phase_n_for, b], "start_tick": block_start_tick, "end_tick": block_start_tick + block_beats * tpb, "mode": fam,
		"length_bars": block_beats / 4, "pads": pads, "phase": phase_n_for, "block": b})
	level.duration_ticks = maxi(level.duration_ticks, block_start_tick + block_beats * tpb)
	_blocks_total += 1
	judge.sync_notes()
	_emit({"kind": "cues", "phase": phase_n_for, "block": b, "family": fam, "count": added.size(), "first": level.notes.size() - added.size()})


## Global beat index of the first beat of phase number `n` (1-based): the current phase (`phase_n`) starts at `phase_t0`; the next one 64 beats later.
func phase_n_for_first_beat(n: int) -> int:
	return int(round(phase_t0 / beat_s)) + (n - phase_n) * int(timing("phase_beats"))


## Block `b` credit summary for tests and the HUD.
func progress_in_block(t: float) -> float:
	return clampf((t - t_of(float(block) * timing("block_beats"))) / (timing("block_beats") * beat_s), 0.0, 1.0)


## Clock-to-beat helper: the phase beat (0..64) a song time falls in.
func phase_beat_at(t: float) -> float:
	return (t - phase_t0) / beat_s


## The pad strip's meter: the current block's cues and the credit earned so far (an empty dictionary outside a cue span).
func progress_at(_t: float) -> Dictionary:
	if level == null or block > 3:
		return {}
	var n := 0
	var got := 0.0
	var done := 0
	for i in range(level.notes.size() - 1, -1, -1):
		var note: Dictionary = level.notes[i]
		if int(note["phase"]) < phase_n:
			break
		if int(note["phase"]) == phase_n and int(note["block"]) == block:
			n += 1
			if judge.is_resolved(i):
				done += 1
				got += judge.credit[i]
	if n == 0:
		return {}
	return {"index": block, "cues": n, "resolved": done, "credit": got}


## RunAudio measured that a part (drums, or bass with the synth) actually started `offset` seconds after its nominal grid time: its cues in this phase
## move by the change, so they sit on what the player hears. Cues already resolved keep their result.
func apply_part_offset(part: String, phase: int, offset: float) -> void:
	if phase != phase_n or not part_offset.has(part):
		return
	var delta := offset - float(part_offset[part])
	part_offset[part] = offset
	var fam_ok := (func(f: String) -> bool: return f == "kick" or f == "snare") if part == "drums" else (func(f: String) -> bool: return f == "bass")
	for i in range(level.notes.size() - 1, -1, -1):
		var n: Dictionary = level.notes[i]
		if int(n["phase"]) < phase_n:
			break
		if fam_ok.call(str(n["family"])) and not judge.is_resolved(i):
			n["time"] = float(n["time"]) + delta
			n["end_time"] = float(n["end_time"]) + delta
