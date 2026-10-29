class_name Match
extends RefCounted
## One play-through of a level: judgement (side 0 rewards), the authored enemy schedule (side 1) and the battle
## simulation, advanced in lock-step with the song clock. Owns the music-mix decisions (which human stems are
## audible) and lane availability. No nodes, so the autoplay harness can drive it headless.
##
## Per simulation tick: player rewards judged before the tick's end time, then enemy events scheduled before it,
## then the tick (combat, repair, destruction) and the outcome. Once an outcome exists nothing later is processed.

var level: Level
var rules: Rules
var judge := Judge.new()
var sim := BattleSim.new()
var sim_ticks := 0
var outcome := ""
var outcome_reason := ""
var outcome_time := -1.0
var stems_muted := {"kick": false, "snare": false, "bass": false, "other": false}
## Schema 2: false is the rhythm-only playtest (no battlefield, no waves, nothing produced); the chart is judged and
## the run ends at duration_ticks with outcome "complete".
var battle_enabled := true
## Schema 2 production state: the equipped profiles' recipes advance one step per successful available reward.
var catalogue: Catalogue
var slot_counter: Dictionary = {}  # slot id -> recipe steps taken this run
var slot_available: Dictionary = {}  # slot id -> bool (every required producer alive)
var group_seq := 0
var point_cursor := 0  # next defense point index; advances once per successfully queued group
var wave_stats: Dictionary = {}  # wave id -> {spawned, killed, first_spawn_s, reached_s, cleared_s}
var _spawn_plan: Array = []  # [{time, wave, actor, entry, via, objective}] sorted by time
var _spawn_index := 0
var _wave_of: Dictionary = {}  # entity id -> wave id
var _pending_rewards: Array = []  # {lane, button, time}
var _enemy_index := 0
var _events: Array = []  # presentation events (sim events plus mix/lane changes)
var production_log: Array = []  # [{time, side, action, result}]


func setup(p_level: Level, p_rules: Rules = null, p_battle := true) -> void:
	level = p_level
	battle_enabled = p_battle
	production_log.clear()
	if level.is_defense():
		_setup_defense(p_rules)
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
	var r := judge.press(button, t, touch_id)
	return r


func release(button: int, t: float, touch_id: int = 0) -> Dictionary:
	if not outcome.is_empty():
		return {"kind": "ended"}
	return judge.release(button, t, touch_id)


func pause_interrupt() -> void:
	judge.void_active_holds()


func drain_events() -> Array:
	var out := _events
	_events = []
	return out


## Advance everything to song time `t` (seconds). Judge events for the frame are returned for lane feedback.
func advance(t: float) -> Array:
	if not outcome.is_empty():
		return []
	if level.is_defense():
		return _advance_defense(t)
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


func _setup_defense(p_rules: Rules) -> void:
	stems_muted = {}
	for key in level.stems:
		stems_muted[key] = false
	judge.setup(level.notes)
	sim_ticks = 0
	_pending_rewards.clear()
	_events.clear()
	outcome = ""
	outcome_reason = ""
	outcome_time = -1.0
	slot_counter = {}
	slot_available = {}
	group_seq = 0
	point_cursor = 0
	wave_stats = {}
	_spawn_plan = []
	_spawn_index = 0
	_wave_of = {}
	catalogue = Catalogue.load_default()
	for slot in level.loadout:
		slot_counter[slot] = 0
		slot_available[slot] = true
	if not battle_enabled:
		return
	rules = p_rules if p_rules != null else Rules.load_default(level.roster if not level.roster.is_empty() else "openra_mvp_01",
		level.battlefield if not level.battlefield.is_empty() else "defense_01")
	sim.setup(rules, level.rules, level.seed)
	for w in (level.waves if level.play_mode != "practice" else []):  # practice charts have no waves
		var wave_id := str(w["id"])
		wave_stats[wave_id] = {"spawned": 0, "killed": 0, "total": 0, "first_spawn_s": -1.0, "reached_s": -1.0, "cleared_s": -1.0}
		for g in w["groups"]:
			var spacing := int(g.get("spawn_spacing_ticks", 0))
			for i in int(g["count"]):
				_spawn_plan.append({"time": level.tick_to_seconds(int(w["start_tick"]) + i * spacing), "wave": wave_id, "actor": str(g["actor"]),
					"entry": str(w["entry"]), "via": str(w["via_defense_point"]), "objective": str(w["target_objective"])})
				wave_stats[wave_id]["total"] += 1
	_spawn_plan.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["time"] < b["time"])


## Equipped profile of a slot (the loadout the level was loaded with).
func profile_of(slot: String) -> String:
	return str(level.loadout.get(slot, ""))


func _advance_defense(t: float) -> Array:
	judge.update(t)
	var judge_events := judge.drain_events()
	for ev in judge_events:
		if ev.get("reward", false):
			_pending_rewards.append(ev)
	if battle_enabled:
		# the deadline tick: nothing after duration_ticks is simulated, so survival resolves exactly there
		var last_tick := int(floor(level.duration_seconds() / BattleSim.TICK_S))
		var target_ticks := mini(int(floor(maxf(t, 0.0) / BattleSim.TICK_S)), last_tick)
		while sim_ticks < target_ticks and outcome.is_empty():
			var tick_end := float(sim_ticks + 1) * BattleSim.TICK_S
			_apply_defense_rewards_before(tick_end)
			_apply_waves_before(tick_end)
			sim.tick()
			sim_ticks += 1
			var now := float(sim_ticks) * BattleSim.TICK_S
			_track_waves(now)
			_process_defense_events(now)
			_update_slots(now)
		if outcome.is_empty() and t >= level.duration_seconds():
			sim.end_by_song()
			_process_defense_events(t)
		return judge_events
	if not battle_enabled:
		while not _pending_rewards.is_empty():
			var r: Dictionary = _pending_rewards.pop_front()
			production_log.append({"time": r["time"], "slot_id": r["slot_id"], "button": int(r["button"]), "source_note_id": r["source_note_id"], "result": "rhythm_only"})
		if t >= level.duration_seconds():
			outcome = "complete"
			outcome_reason = "rhythm_only"
			outcome_time = t
		return judge_events
	return judge_events


## One successful, available reward: resolve its slot to the equipped profile and take the next recipe step.
## The counter and the defense-point cycle advance only when a group is actually queued.
func _apply_defense_rewards_before(tick_end: float) -> void:
	while not _pending_rewards.is_empty() and _pending_rewards[0]["time"] < tick_end:
		var r: Dictionary = _pending_rewards.pop_front()
		var slot := str(r["slot_id"])
		var profile := profile_of(slot)
		var steps := catalogue.steps(profile)
		var entry := {"time": r["time"], "slot_id": slot, "profile_id": profile, "button": int(r["button"]), "source_note_id": r["source_note_id"]}
		if catalogue.production_type(profile) != "cycle" or steps.is_empty():
			entry["result"] = "unsupported_recipe"
		else:
			var step: Dictionary = steps[int(slot_counter[slot]) % steps.size()]
			var res := sim.produce_group(0, step["units"], group_seq + 1, point_cursor)
			entry["result"] = res["result"]
			if res["result"] == "queued":
				group_seq += 1
				point_cursor += 1
				slot_counter[slot] = int(slot_counter[slot]) + 1
				entry["group_id"] = res["group_id"]
				entry["point"] = res["point"]
				entry["point_id"] = res["point_id"]
				entry["units"] = res["actors"]
			_events.append({"kind": "group", "result": res["result"], "slot_id": slot, "button": int(r["button"]), "group_id": entry.get("group_id", -1), "point": entry.get("point", -1)})
		production_log.append(entry)


## Enemy waves are scheduled by song time and spawn with no producer, whatever the player did.
func _apply_waves_before(tick_end: float) -> void:
	while _spawn_index < _spawn_plan.size() and _spawn_plan[_spawn_index]["time"] < tick_end:
		var sp: Dictionary = _spawn_plan[_spawn_index]
		var u := sim.spawn_wave_unit(sp["actor"], sp["entry"], sp["via"], sp["objective"])
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


## Per-slot producer gating: a slot is available while every producer its profile needs is alive. An unavailable
## slot's notes become inert (judge) and its stem is muted; both are restored in place when the producers return.
## A change of input focus never touches this.
func _update_slots(now: float) -> void:
	for slot in level.loadout:
		var ok := true
		for tag in catalogue.required_producers(profile_of(slot)):
			var role: String = Catalogue.PRODUCER_ROLE.get(tag, "")
			if role == "pad":
				ok = ok and sim.pads_alive(0) > 0
			elif role.is_empty() or not sim.producer_alive(0, role):
				ok = false
		if slot_available[slot] != ok:
			slot_available[slot] = ok
			judge.set_slot_available(slot, ok)
			_set_stem(slot, not ok, now)


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


func _set_stem(key: String, muted: bool, now: float) -> void:
	if stems_muted[key] == muted:
		return
	stems_muted[key] = muted
	_events.append({"kind": "stem", "stem": key, "muted": muted, "time": now})


## The next wave that has not started yet: {id, number, in_s, entry, via, objective}, or {} when none is left.
func upcoming_wave() -> Dictionary:
	var now := float(sim_ticks) * BattleSim.TICK_S
	if level.play_mode == "practice":
		return {}
	for i in level.waves.size():
		var w: Dictionary = level.waves[i]
		var start := level.tick_to_seconds(int(w["start_tick"]))
		if start > now:
			return {"id": w["id"], "number": i + 1, "in_s": start - now, "entry": w["entry"], "via": w["via_defense_point"], "objective": w["target_objective"]}
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
	if level.is_defense():
		return {
			"mode": "defense",
			"outcome": outcome if not outcome.is_empty() else "incomplete",
			"reason": outcome_reason,
			"level": level.title,
			"level_id": level.level_id,
			"chart_id": level.chart_id,
			"play_mode": level.play_mode,
			"progression": level.progression,
			"campaign_level": level.campaign_level,
			"accuracy": judge.accuracy(),
			"perfect": judge.perfect,
			"good": judge.good,
			"misses": judge.misses,
			"strays": judge.strays,
			"best_combo": judge.best_combo,
			"judged": judge.judged_count(),
			"rewards": judge.rewards.duplicate(),
			"battle": battle_enabled,
			"outcome_time_s": outcome_time,
			"groups": group_seq,
			"slot_counters": slot_counter.duplicate(),
			"objective_hp": _objective_report(),
			"waves": wave_stats.duplicate(true),
			"produced": sim.stats["produced"].duplicate(true) if battle_enabled else [],
			"lost": sim.stats["lost"].duplicate(true) if battle_enabled else [],
			"battle_time_s": float(sim_ticks) * BattleSim.TICK_S,
		}
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
