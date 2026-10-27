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
var _pending_rewards: Array = []  # {lane, button, time}
var _enemy_index := 0
var _events: Array = []  # presentation events (sim events plus mix/lane changes)
var production_log: Array = []  # [{time, side, action, result}]


func setup(p_level: Level, p_rules: Rules = null) -> void:
	level = p_level
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


func result() -> Dictionary:
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
