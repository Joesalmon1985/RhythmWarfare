class_name Match
extends RefCounted
## One play-through of a level, advanced in lock-step with the song clock, with no nodes so the autoplay harness can
## drive it headless. Missions (schema 3): pad recognition -> sequences -> scheduled rewards, authored waves by song
## time, the defense simulation. The legacy duel (schema 1): per-note rewards, the enemy schedule, the two-sided battle.
##
## Per simulation tick: sequence results (or duel rewards) resolved before the tick's end time, then waves (or enemy
## events) scheduled before it, then the tick (combat, repair, destruction) and the outcome. Once an outcome exists
## nothing later is processed.

var level: Level
var rules: Rules
var judge := Judge.new()
var sim := BattleSim.new()
var sim_ticks := 0
var outcome := ""
var outcome_reason := ""
var outcome_time := -1.0
var stems_muted := {"kick": false, "snare": false, "bass": false, "other": false}
## Missions: false is practice / the rhythm-only playtest (no battlefield, no waves, nothing built); the cues are judged,
## the sequences resolved, and the run ends at duration_ticks with outcome "complete".
var battle_enabled := true
var wave_stats: Dictionary = {}  # wave id -> {spawned, killed, first_spawn_s, reached_s, cleared_s}
var _spawn_plan: Array = []  # [{time, wave, actor, entry, via, objective, target}] sorted by time
var _warn_plan: Array = []   # [{time, wave, entry}] sorted by time: one "wave_warning" per wave, WAVE_WARNING_S ahead
var _warn_index := 0
var _spawn_index := 0
var _wave_of: Dictionary = {}  # entity id -> wave id
var _pending_rewards: Array = []  # {lane, button, time}
var _enemy_index := 0
var _events: Array = []  # presentation events (sim events plus mix/lane changes)
var production_log: Array = []  # [{time, side, action, result}]
## Schema 3 (missions): cue recognition on the pads, sequence results and the rewards they schedule.
var pad_judge := PadJudge.new()
var tracker := SequenceTracker.new()
var reward_log: Array = []  # [{sequence, reward, grade, delay_s, resolve_time, ready_time, result, kind, point, label}]
var _resolved: Array = []  # sequence results waiting for the tick that contains their resolve time
var _mission_phase := -1  # the phase (section index) the last advance was in
var _phase_families: Array = []  # per phase: {family: true} for every family with a cue in it
var _program_bar := -1  # the bar whose gain program was last emitted (missions)

const WAVE_WARNING_S := 8.0  # the "wave_warning" event comes this long before a wave's first unit appears


func setup(p_level: Level, p_rules: Rules = null, p_battle := true) -> void:
	level = p_level
	battle_enabled = p_battle
	production_log.clear()
	if level.is_mission():
		_setup_mission(p_rules)
		return
	rules = p_rules if p_rules != null else Rules.load_default(level.roster if not level.roster.is_empty() else "openra_mvp_01",
		level.battlefield if not level.battlefield.is_empty() else "mvp_mirrored_01")
	judge.setup(level.notes)
	sim.setup(rules, level.rules, level.seed)
	sim_ticks = 0
	_enemy_index = 0
	_pending_rewards.clear()
	_events.clear()
	outcome = ""


## A press or release on one of the four buttons (1 to 4).
func press(button: int, t: float, touch_id: int = 0) -> Dictionary:
	if not outcome.is_empty():
		return {"kind": "ended"}
	if level.is_mission():
		return pad_judge.press(button, t, touch_id)
	var r := judge.press(button, t, touch_id)
	return r


func release(button: int, t: float, touch_id: int = 0) -> Dictionary:
	if not outcome.is_empty():
		return {"kind": "ended"}
	if level.is_mission():
		return pad_judge.release(button, t, touch_id)
	return judge.release(button, t, touch_id)


## Pause: an active hold ends where it stands (coverage so far); `t` is the frozen song time.
func pause_interrupt(t: float = 0.0) -> void:
	if level.is_mission():
		pad_judge.pause_interrupt(t)
		return
	judge.void_active_holds()


func drain_events() -> Array:
	var out := _events
	_events = []
	return out


## Advance everything to song time `t` (seconds). Judge events for the frame are returned for lane feedback.
func advance(t: float) -> Array:
	if not outcome.is_empty():
		return []
	if level.is_mission():
		return _advance_mission(t)
	judge.update(t)
	var judge_events := judge.drain_events()
	for ev in judge_events:
		if ev.get("reward", false):
			_pending_rewards.append({"lane": ev["lane"], "button": int(ev.get("button", 0)), "time": ev["time"]})
	var target_ticks := int(floor(maxf(t, 0.0) / BattleSim.TICK_S))
	while sim_ticks < target_ticks and outcome.is_empty():
		var tick_end := float(sim_ticks + 1) * BattleSim.TICK_S
		_apply_rewards_before(tick_end)
		_apply_enemy_before(tick_end)
		sim.tick()
		sim_ticks += 1
		_process_sim_events(float(sim_ticks) * BattleSim.TICK_S)
	if outcome.is_empty() and t >= level.duration_seconds():
		sim.end_by_song()
		_process_sim_events(t)
	return judge_events


# --- schema 3: missions -------------------------------------------------------------------------------------------

func _setup_mission(p_rules: Rules) -> void:
	stems_muted = {}
	for key in level.stems:
		stems_muted[key] = false
	pad_judge.setup(level.notes, level.sequences)
	tracker.setup(level, pad_judge)
	_mission_phase = -1
	_program_bar = -1
	_phase_families = []
	for _i in level.sections.size():
		_phase_families.append({})
	for n in level.notes:
		var ph := _phase_index(int(n["tick"]))
		if ph >= 0:
			_phase_families[ph][str(n.get("family", n.get("lane", "")))] = true
	reward_log = []
	_resolved = []
	sim_ticks = 0
	_events.clear()
	outcome = ""
	outcome_reason = ""
	outcome_time = -1.0
	wave_stats = {}
	_spawn_plan = []
	_spawn_index = 0
	_warn_plan = []
	_warn_index = 0
	_wave_of = {}
	if not battle_enabled:
		return
	rules = p_rules if p_rules != null else Rules.load_default(level.roster, level.battlefield)
	sim.setup(rules, level.rules, level.seed)
	for w in level.waves:
		var wave_id := str(w["id"])
		wave_stats[wave_id] = {"spawned": 0, "killed": 0, "total": 0, "first_spawn_s": -1.0, "reached_s": -1.0, "cleared_s": -1.0}
		_warn_plan.append({"time": level.tick_to_seconds(int(w["start_tick"])), "wave": wave_id, "entry": str(w["entry"])})
		for g in w["groups"]:
			var spacing := int(g.get("spawn_spacing_ticks", 0))
			var target := str(g.get("target", w.get("target", "core")))  # a group may override its wave's target class
			for i in int(g["count"]):
				_spawn_plan.append({"time": level.tick_to_seconds(int(w["start_tick"]) + i * spacing), "wave": wave_id, "actor": str(g["actor"]),
					"entry": str(w["entry"]), "via": str(w["via_defense_point"]), "objective": str(w["target_objective"]), "target": target})
				wave_stats[wave_id]["total"] += 1
	_spawn_plan.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["time"] < b["time"])
	_warn_plan.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["time"] < b["time"])


func _advance_mission(t: float) -> Array:
	_emit_program(t)
	pad_judge.update(t)
	var judge_events := pad_judge.drain_events()
	_judge_to_stems(judge_events, t)
	for r in tracker.update():
		_resolved.append(r)
		_events.append({"kind": "sequence", "result": r})
	if battle_enabled:
		var last_tick := int(floor(level.duration_seconds() / BattleSim.TICK_S))
		var target_ticks := mini(int(floor(maxf(t, 0.0) / BattleSim.TICK_S)), last_tick)
		while sim_ticks < target_ticks and outcome.is_empty():
			var tick_end := float(sim_ticks + 1) * BattleSim.TICK_S
			_apply_sequences_before(tick_end)
			_apply_wave_warnings_before(tick_end)
			_apply_waves_before(tick_end)
			sim.tick()
			sim_ticks += 1
			var now := float(sim_ticks) * BattleSim.TICK_S
			_track_waves(now)
			_process_defense_events(now)
		if outcome.is_empty() and t >= level.duration_seconds():
			sim.end_by_song()
			_process_defense_events(t)
		return judge_events
	while not _resolved.is_empty():
		var r: Dictionary = _resolved.pop_front()
		reward_log.append({"sequence": r["index"], "reward": r["reward"], "passed": r["passed"], "grade": r["grade"], "result": "practice"})
	if t >= level.duration_seconds():
		outcome = "complete"
		outcome_reason = "rhythm_only"
		outcome_time = t
	return judge_events


## The mission's gain program: when the song enters a new bar (and once at the first frame) one {"kind": "program", "on":
## {stem key: bool}} event says which stems sound. The transport combines it with the miss mutes.
func _emit_program(t: float) -> void:
	if level.gain_program.is_empty():
		return
	var bar := clampi(level.seconds_to_tick(maxf(t, 0.0)) / level.ticks_per_bar(), 0, level.gain_program.size() - 1)
	if bar == _program_bar:
		return
	_program_bar = bar
	_events.append({"kind": "program", "on": (level.gain_program[bar] as Dictionary).duplicate(), "bar": bar})


## A passed sequence schedules its one reward at resolve time + the precision delay, on the tick that contains its
## resolve time (so placement never depends on the frame rate). A failed one earns nothing.
func _apply_sequences_before(tick_end: float) -> void:
	while not _resolved.is_empty() and float(_resolved[0]["resolve_time"]) < tick_end:
		var r: Dictionary = _resolved.pop_front()
		var entry := {"sequence": r["index"], "reward": r["reward"], "passed": r["passed"], "grade": r["grade"], "delay_s": r["delay_s"],
			"resolve_time": r["resolve_time"], "credit": r["credit"]}
		if r["passed"]:
			var ready := float(r["resolve_time"]) + float(r["delay_s"])
			entry["ready_time"] = ready
			var res := sim.schedule_reward(str(r["reward"]), int(ceil(ready / BattleSim.TICK_S)), _next_wave_point())
			entry["result"] = res["result"]
			entry["kind"] = res.get("kind", "")
			entry["point"] = res.get("point", -1)
			entry["label"] = res.get("label", "")
			entry["capacity"] = res.get("capacity", false)
		else:
			entry["result"] = "failed"
		reward_log.append(entry)


## The reward placement hint: the defense point most enemies are walking towards now, else the one the next wave
## walks through, -1 when none is left.
func _next_wave_point() -> int:
	var live := sim.approaching_point()
	if live >= 0:
		return live
	var now := float(sim_ticks) * BattleSim.TICK_S
	for w in level.waves:
		if level.tick_to_seconds(int(w["start_tick"])) + 4.0 > now:
			for i in sim.defense_points.size():
				if sim.defense_points[i]["id"] == str(w["via_defense_point"]):
					return i
	return -1


## The section a tap would most usefully pick now: where the next wave comes through, else the section already
## active, else the one holding the fewest defenders. -1 when the level has no sections.
func suggest_point() -> int:
	if not battle_enabled or sim.defense_points.is_empty():
		return -1
	var hint := _next_wave_point()
	if hint >= 0:
		return hint
	if sim.active_point >= 0:
		return sim.active_point
	var best := 0
	var best_n := 1 << 30
	for i in sim.defense_points.size():
		var n := sim.units_at(i)
		if n < best_n:
			best = i
			best_n = n
	return best


## The player taps a section: new rewards deploy to it while it has room (-1 clears the choice). Emits a "section"
## event {point, id} for the view. Returns false for an index that is not a section.
func set_active_point(i: int) -> bool:
	if not battle_enabled or not outcome.is_empty() or i < -1 or i >= sim.defense_points.size():
		return false
	sim.active_point = i
	_events.append({"kind": "section", "point": i, "id": str(sim.defense_points[i]["id"]) if i >= 0 else ""})
	return true


## The section new rewards deploy to now: the tapped one, else the suggested one (0 if there is no suggestion).
## -1 when the level has no sections.
func rally_point() -> int:
	if sim.defense_points.is_empty():
		return -1
	if sim.active_point >= 0:
		return sim.active_point
	return maxi(suggest_point(), 0)


## The name shown for the primary objective on the result screen.
func _objective_name(id: String) -> String:
	match sim.objective_role(id):
		"main":
			return "Command core"
		"barracks":
			return "Barracks"
		"power":
			return "Power plant"
		"dome":
			return "Radar dome"
		"factory":
			return "War factory"
	return id.replace("_", " ").capitalize()


func _mission_result() -> Dictionary:
	var grades := tracker.grade_counts()
	var built := 0
	var units := 0
	var repairs := 0
	for e in reward_log:
		match str(e.get("kind", "")):
			"build":
				built += 1
			"unit":
				units += 1
			"repair":
				repairs += 1
	var abs_sum := 0.0
	var signed_sum := 0.0
	var n := 0
	for i in pad_judge.notes.size():
		if not is_nan(pad_judge.delta_ms[i]):
			abs_sum += absf(pad_judge.delta_ms[i])
			signed_sum += pad_judge.delta_ms[i]
			n += 1
	return {
		"mode": "mission",
		"outcome": outcome if not outcome.is_empty() else "incomplete",
		"reason": outcome_reason,
		"level": level.title,
		"level_id": level.level_id,
		"play_mode": level.play_mode,
		"progression": level.progression,
		"campaign_level": level.campaign_level,
		"battle": battle_enabled,
		"loadout": level.loadout.duplicate(true),
		"accuracy": pad_judge.accuracy(),
		"cues": pad_judge.notes.size(),
		"perfect": pad_judge.perfect,
		"great": pad_judge.great,
		"ok": pad_judge.ok,
		"misses": pad_judge.misses,
		"strays": pad_judge.strays,
		"holds_complete": pad_judge.holds_complete,
		"holds_partial": pad_judge.holds_partial,
		"best_combo": pad_judge.best_combo,
		"mean_abs_ms": abs_sum / float(n) if n > 0 else 0.0,
		"mean_ms": signed_sum / float(n) if n > 0 else 0.0,
		"sequences": level.sequences.size(),
		"sequences_passed": tracker.passed_count(),
		"grades": grades,
		"built": built,
		"units": units,
		"repairs": repairs,
		"defenses_alive": sim.defense_count() if battle_enabled else 0,
		"reward_log": reward_log.duplicate(true),
		"outcome_time_s": outcome_time,
		"objective_hp": _objective_report(),
		"primary_objective": sim.primary_objective_id() if battle_enabled else "",
		"primary_objective_name": _objective_name(sim.primary_objective_id()) if battle_enabled and not sim.primary_objective_id().is_empty() else "",
		"villagers_total": int(sim.stats["civilians_total"]) if battle_enabled else 0,
		"villagers_lost": int(sim.stats["civilians_lost"]) if battle_enabled else 0,
		"houses_total": int(sim.stats["houses_total"]) if battle_enabled else 0,
		"houses_lost": int(sim.stats["houses_lost"]) if battle_enabled else 0,
		"waves": wave_stats.duplicate(true),
		"produced": sim.stats["produced"].duplicate(true) if battle_enabled else [],
		"lost": sim.stats["lost"].duplicate(true) if battle_enabled else [],
		"battle_time_s": float(sim_ticks) * BattleSim.TICK_S,
	}


## Once per wave, WAVE_WARNING_S before its first unit appears (at once for a wave that starts sooner than that).
func _apply_wave_warnings_before(tick_end: float) -> void:
	while _warn_index < _warn_plan.size() and float(_warn_plan[_warn_index]["time"]) - WAVE_WARNING_S < tick_end:
		var w: Dictionary = _warn_plan[_warn_index]
		_warn_index += 1
		_events.append({"kind": "wave_warning", "wave": w["wave"], "entry": w["entry"], "in_s": maxf(float(w["time"]) - tick_end, 0.0)})


## Enemy waves are scheduled by song time and spawn with no producer, whatever the player did.
func _apply_waves_before(tick_end: float) -> void:
	while _spawn_index < _spawn_plan.size() and _spawn_plan[_spawn_index]["time"] < tick_end:
		var sp: Dictionary = _spawn_plan[_spawn_index]
		var u := sim.spawn_wave_unit(sp["actor"], sp["entry"], sp["via"], sp["objective"], sp["target"])
		if u == null:
			return  # entry cell occupied: retry next tick, keep the authored order
		_spawn_index += 1
		_wave_of[u.id] = sp["wave"]
		var st: Dictionary = wave_stats[sp["wave"]]
		st["spawned"] += 1
		if st["first_spawn_s"] < 0.0:
			st["first_spawn_s"] = float(sim_ticks + 1) * BattleSim.TICK_S
			_events.append({"kind": "wave", "wave": sp["wave"], "entry": sp["entry"], "time": st["first_spawn_s"]})


## Per tick: when did each wave first get near the base, and when was it wiped out.
func _track_waves(now: float) -> void:
	for id in _wave_of.keys():
		var u: BattleSim.Ent = sim.get_entity(int(id))
		var st: Dictionary = wave_stats[_wave_of[id]]
		if u != null and u.alive and st["reached_s"] < 0.0 and u.x <= 15.5:
			st["reached_s"] = now
	for wave_id in wave_stats:
		var st: Dictionary = wave_stats[wave_id]
		if st["cleared_s"] < 0.0 and st["spawned"] == st["total"] and st["total"] > 0 and st["killed"] >= st["total"]:
			st["cleared_s"] = now


func _process_defense_events(now: float) -> void:
	for ev in sim.drain_events():
		_events.append(ev)
		match ev["kind"]:
			"destroyed":
				if int(ev["side"]) == 1 and _wave_of.has(ev["id"]):
					wave_stats[_wave_of[ev["id"]]]["killed"] += 1
			"outcome":
				outcome = ev["outcome"]
				outcome_reason = ev["reason"]
				outcome_time = now


func _apply_rewards_before(tick_end: float) -> void:
	while not _pending_rewards.is_empty() and _pending_rewards[0]["time"] < tick_end:
		var r: Dictionary = _pending_rewards.pop_front()
		var res := sim.produce(0, r["lane"])
		production_log.append({"time": r["time"], "side": 0, "action": r["lane"], "result": res["result"]})
		_events.append({"kind": "production", "side": 0, "action": r["lane"], "button": r["button"], "result": res})


func _apply_enemy_before(tick_end: float) -> void:
	while _enemy_index < level.enemy_events.size() and level.enemy_events[_enemy_index]["time"] < tick_end:
		var e: Dictionary = level.enemy_events[_enemy_index]
		_enemy_index += 1
		var res := sim.produce(1, e["action"])
		production_log.append({"time": e["time"], "side": 1, "action": e["action"], "result": res["result"], "id": e["id"]})
		_events.append({"kind": "production", "side": 1, "action": e["action"], "result": res})


func _process_sim_events(now: float) -> void:
	for ev in sim.drain_events():
		_events.append(ev)
		match ev["kind"]:
			"producer_lost":
				if ev["side"] == 0:
					if ev["role"] == "factory":
						_set_stem("kick", true, now)
						judge.set_lane_available("kick", false)
					elif ev["role"] == "barracks":
						_set_stem("snare", true, now)
						judge.set_lane_available("snare", false)
			"pad_lost":
				if ev["side"] == 0 and int(ev["pads_alive"]) == 0:
					_set_stem("bass", true, now)
			"pad_built":
				if ev["side"] == 0:
					_set_stem("bass", false, now)
			"outcome":
				outcome = ev["outcome"]
				outcome_reason = ev["reason"]
				outcome_time = now


## Index of the phase (section) at a song tick, -1 outside the song.
func _phase_index(tick: int) -> int:
	for i in level.sections.size():
		if tick >= int(level.sections[i]["start_tick"]) and tick < int(level.sections[i]["end_tick"]):
			return i
	return -1


## Missions: a missed cue (or a hold let go with no coverage) silences its instrument's stem until the next hit on it
## (a tap of any grade, a completed or partly held hold). The backing track ("other") never mutes. When the phase
## changes, every family the new phase does not cue is back. A miss resolving after the phase moved on, for a family
## the new phase does not cue, mutes nothing. Runs inside the frame's advance, so the "stem" events reach the player in
## the same frame as the judge events.
func _judge_to_stems(judge_events: Array, t: float) -> void:
	var phase := _phase_index(level.seconds_to_tick(maxf(t, 0.0)))
	if phase != _mission_phase:
		_mission_phase = phase
		var cued: Dictionary = _phase_families[phase] if phase >= 0 else {}
		for fam in ["kick", "snare", "bass"]:
			if not cued.has(fam):
				_set_family(fam, false, t)
	var cued_now: Dictionary = _phase_families[phase] if phase >= 0 else {}
	for ev in judge_events:
		var fam := str(ev.get("family", ""))
		if fam.is_empty() or fam == "other":
			continue
		var when := float(ev.get("time", t))
		match str(ev.get("kind", "")):
			"miss", "hold_fail":
				if cued_now.has(fam):
					_set_family(fam, true, when)
			"hold_partial":
				if float(ev.get("coverage", 0.0)) > 0.0:
					_set_family(fam, false, when)
				elif cued_now.has(fam):
					_set_family(fam, true, when)
			"perfect", "great", "ok", "good", "hold_complete":
				_set_family(fam, false, when)


## Mutes or restores every stem of an instrument family (a pack may carry several per family; "other" never mutes).
func _set_family(family: String, muted: bool, now: float) -> void:
	if family == "other":
		return
	for key in stems_muted:
		if _stem_has_family(key, family):
			_set_stem(key, muted, now)


## True while any stem of the family is silenced by a miss (for the pad labels).
func family_muted(family: String) -> bool:
	for key in stems_muted:
		if _stem_has_family(key, family) and bool(stems_muted[key]):
			return true
	return false


## Whether a stem carries an instrument family: its own family, or one of the several a recorded mix carries.
func _stem_has_family(key: String, family: String) -> bool:
	if level.stem_families.has(key):
		return family in level.stem_families[key]
	return str(level.stem_family.get(key, key)) == family


func _set_stem(key: String, muted: bool, now: float) -> void:
	if not stems_muted.has(key) or stems_muted[key] == muted:
		return
	stems_muted[key] = muted
	_events.append({"kind": "stem", "stem": key, "muted": muted, "time": now})


## The next wave that has not started yet: {id, number, in_s, entry, via, objective, target}, or {} when none is left.
func upcoming_wave() -> Dictionary:
	var now := float(sim_ticks) * BattleSim.TICK_S
	if not battle_enabled:
		return {}
	for i in level.waves.size():
		var w: Dictionary = level.waves[i]
		var start := level.tick_to_seconds(int(w["start_tick"]))
		if start > now:
			return {"id": w["id"], "number": i + 1, "in_s": start - now, "entry": w["entry"], "via": w["via_defense_point"],
				"objective": w["target_objective"], "target": str(w.get("target", "core"))}
	return {}


## Living defenders per defense point, in point order.
func defenders_per_point() -> Array:
	var out := []
	for i in sim.defense_points.size():
		out.append(0)
	for e in sim.entities:
		if e.alive and e.side == 0 and e.kind == BattleSim.Kind.UNIT and e.group >= 0 and sim.groups.has(e.group):
			out[int(sim.groups[e.group]["point"])] += 1
	return out


func _objective_report() -> Dictionary:
	var out := {}
	if battle_enabled:
		for o in sim.objectives:
			out[o["id"]] = {"hp": sim.objective_hp(o["id"]), "max": sim.objective_max_hp(o["id"])}
	return out


func result() -> Dictionary:
	if level.is_mission():
		return _mission_result()
	return {
		"outcome": outcome if not outcome.is_empty() else "incomplete",
		"reason": outcome_reason,
		"level": level.title,
		"accuracy": judge.accuracy(),
		"perfect": judge.perfect,
		"good": judge.good,
		"misses": judge.misses,
		"strays": judge.strays,
		"best_combo": judge.best_combo,
		"judged": judge.judged_count(),
		"rewards": judge.rewards.duplicate(),
		"produced": sim.stats["produced"].duplicate(true),
		"lost": sim.stats["lost"].duplicate(true),
		"air_busy": sim.stats["air_busy"].duplicate(),
		"battle_time_s": float(sim_ticks) * BattleSim.TICK_S,
		"outcome_time_s": outcome_time,
	}
