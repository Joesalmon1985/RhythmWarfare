extends SceneTree
## Headless balance harness (acceptance A08, A12): plays a level with a scripted input policy against its authored
## enemy schedule, with no audio and no rendering, and prints the trace.
##
##   godot --headless --path . -s tools/autoplay.gd -- <pack dir> [policy] [enemy_fraction] [seed] [chart id]
## Schema 2 (defense) packs: enemy_fraction is ignored, seed also seeds the simulation, and the report adds the
## objective health, every wave's spawn / arrival / clear times, the production log summary and the group cycle.
##
## Missions (schema 3) use plan_inputs(): perfect, accuracy:<f>, none, beginner, sloppy (plausible imperfect play with
## timing scatter, misses, early hold releases and stray presses, seeded) and mash (pressing every lit pad every 60 ms).
##
## policy:  perfect            every note hit at its exact time
##          accuracy:<f>       each note hit with probability f (seeded), otherwise ignored
##          none               no input at all
##          perfect_until:<s>  perfect until song second s, nothing after
##          perfect_no_bass    perfect kicks and snares, no bass actions
## enemy_fraction: keep this seeded fraction of the authored enemy events (default 1.0 = the pack as authored)

const FRAME_S := 1.0 / 60.0


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		push_error("usage: <pack dir> [policy] [enemy_fraction] [seed]")
		quit(2)
		return
	var pack: String = args[0]
	var policy: String = args[1] if args.size() > 1 else "perfect"
	var enemy_fraction := float(args[2]) if args.size() > 2 else 1.0
	var seed_value := int(args[3]) if args.size() > 3 else 1
	var chart_id: String = args[4] if args.size() > 4 else ""
	var loaded := LevelLoader.load_pack(pack, {"chart_id": chart_id})
	if loaded["level"] == null:
		push_error("pack rejected: " + str(loaded["errors"]))
		quit(2)
		return
	var level: Level = loaded["level"]
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	if level.is_defense():
		level.seed = level.seed * 10 + seed_value
	if enemy_fraction < 1.0 and not level.is_defense():
		var kept: Array = []
		for e in level.enemy_events:
			if rng.randf() < enemy_fraction:
				kept.append(e)
		level.enemy_events = kept
	var m := Match.new()
	m.setup(level)
	var result := run(m, level, policy, rng)
	print(JSON.stringify(result, "  "))
	quit(0)


static func run(m: Match, level: Level, policy: String, rng: RandomNumberGenerator) -> Dictionary:
	if level.is_mission():
		return run_mission(m, level, policy, rng)
	var hit_prob := 1.0
	var until := INF
	var no_bass := false
	if policy.begins_with("accuracy:"):
		hit_prob = float(policy.substr(9))
	elif policy == "none":
		hit_prob = 0.0
	elif policy.begins_with("perfect_until:"):
		until = float(policy.substr(14))
	elif policy == "perfect_no_bass":
		no_bass = true
	# decide per note up front so the trace is reproducible
	var plan: Array = []
	for n in level.notes:
		var hit: bool = rng.randf() < hit_prob and float(n["time"]) < until and not (no_bass and str(n["lane"]) == "bass")
		plan.append(hit)
	var next_note := 0
	var holding: Dictionary = {}  # button -> end_time
	var t := -1.0
	var peak := [0, 0]
	var timeline: Array = []
	var duration := level.duration_seconds()
	var ticks_done := 0
	var shots := [0, 0]
	var kills := [0, 0]
	var debug_every := float(OS.get_environment("RW_DEBUG_EVERY")) if OS.has_environment("RW_DEBUG_EVERY") else 0.0
	var next_debug := debug_every
	while m.outcome.is_empty() and t < duration + 0.5:
		t += FRAME_S
		# presses due this frame
		while next_note < level.notes.size() and level.notes[next_note]["time"] <= t:
			var n: Dictionary = level.notes[next_note]
			if plan[next_note]:
				m.press(int(n["button"]), n["time"], 1)
				if n["type"] == "hold":
					holding[int(n["button"])] = n["end_time"]
			next_note += 1
		for button in holding.keys():
			if t >= holding[button] + 0.02:
				m.release(button, holding[button] + 0.02, 1)
				holding.erase(button)
		m.advance(t)
		for ev in m.drain_events():
			match ev["kind"]:
				"producer_lost", "pad_lost", "outcome", "stem", "wave":
					timeline.append({"t": snappedf(t, 0.01), "event": ev})
				"shot":
					var shooter: BattleSim.Ent = m.sim.get_entity(ev["from"])
					if shooter != null:
						shots[shooter.side] += 1
				"destroyed":
					kills[1 - int(ev["side"])] += 1
		if debug_every > 0.0 and t >= next_debug:
			next_debug += debug_every
			_debug_line(m, t, shots, kills)
			shots = [0, 0]
			kills = [0, 0]
		if m.sim_ticks != ticks_done:
			ticks_done = m.sim_ticks
			peak[0] = maxi(peak[0], m.sim.count_alive(0, BattleSim.Kind.UNIT))
			peak[1] = maxi(peak[1], m.sim.count_alive(1, BattleSim.Kind.UNIT))
	var r := m.result()
	r["policy"] = policy
	r["debug_every"] = debug_every
	r["peak_live_units"] = peak
	r["song_duration_s"] = duration
	r["player_main_hp"] = m.sim.main_base(0).hp if m.sim.main_base(0) != null else 0
	r["enemy_main_hp"] = m.sim.main_base(1).hp if m.sim.main_base(1) != null else 0
	if level.is_defense():
		r["player_main_hp"] = m.sim.objective_hp("command_core")
	r["enemy_events_used"] = level.enemy_events.size()
	if level.is_defense():
		r["seed"] = level.seed
		r["production_summary"] = _production_summary(m)
	r["timeline"] = timeline
	r["blocked"] = m.sim.stats["blocked"]
	r["profile_ms"] = {}
	for k in m.sim.profile:
		r["profile_ms"][k] = m.sim.profile[k] if k == "ticks" else snappedf(float(m.sim.profile[k]) / 1000.0, 0.1)
	return r


## Input events for a mission: [{t, pad, down}] sorted by time. Deterministic for a seeded rng.
static func plan_inputs(level: Level, policy: String, rng: RandomNumberGenerator) -> Array:
	var ev: Array = []
	var hit_prob := 1.0
	var sigma_ms := 0.0
	var early_release := 0.0
	var stray_rate := 0.0
	var late_bias_ms := 0.0
	match policy:
		"none":
			return []
		"beginner":
			hit_prob = 0.85
			sigma_ms = 55.0
			early_release = 0.3
			stray_rate = 0.12
			late_bias_ms = 15.0
		"sloppy":
			hit_prob = 0.7
			sigma_ms = 85.0
			early_release = 0.5
			stray_rate = 0.25
			late_bias_ms = 25.0
		"mash":
			return _mash_inputs(level)
		_:
			if policy.begins_with("accuracy:"):
				hit_prob = float(policy.substr(9))
	for n in level.notes:
		var t0 := float(n["time"])
		if rng.randf() < stray_rate:
			var ts := t0 - 0.3 + rng.randf() * 0.1
			var sp := 1 + rng.randi() % 4
			ev.append({"t": ts, "pad": sp, "down": true})
			ev.append({"t": ts + 0.05, "pad": sp, "down": false})
		if rng.randf() >= hit_prob:
			continue
		var err := clampf(_gauss(rng) * sigma_ms + late_bias_ms, -130.0, 130.0) / 1000.0 if sigma_ms > 0.0 else 0.0
		var t := t0 + err
		ev.append({"t": t, "pad": int(n["pad"]), "down": true})
		var up := t + 0.08
		if n["type"] == "hold":
			up = float(n["end_time"]) + 0.02
			if rng.randf() < early_release:
				up = t0 + (float(n["end_time"]) - t0) * (0.4 + 0.5 * rng.randf())
		ev.append({"t": up, "pad": int(n["pad"]), "down": false})
	ev.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["t"] < b["t"] if a["t"] != b["t"] else (not a["down"] and b["down"]))
	return ev


static func _mash_inputs(level: Level) -> Array:
	var ev: Array = []
	var t := 0.0
	while t < level.duration_seconds():
		var ph := level.phase_at(level.seconds_to_tick(t))
		for pad in ph.get("pads", {}).keys():
			ev.append({"t": t, "pad": int(pad), "down": true})
			ev.append({"t": t + 0.03, "pad": int(pad), "down": false})
		t += 0.06
	ev.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a["t"] < b["t"])
	return ev


static func _gauss(rng: RandomNumberGenerator) -> float:
	return sqrt(-2.0 * log(maxf(rng.randf(), 1e-9))) * cos(TAU * rng.randf())


static func run_mission(m: Match, level: Level, policy: String, rng: RandomNumberGenerator) -> Dictionary:
	var plan := plan_inputs(level, policy, rng)
	var down := {}
	var k := 0
	var t := -0.5
	var peak := [0, 0]
	var duration := level.duration_seconds()
	var timeline: Array = []
	while m.outcome.is_empty() and t < duration + 0.5:
		t += FRAME_S
		while k < plan.size() and float(plan[k]["t"]) <= t:
			var e: Dictionary = plan[k]
			if e["down"]:
				if not down.get(e["pad"], false):
					down[e["pad"]] = true
					m.press(int(e["pad"]), float(e["t"]), int(e["pad"]))
			elif down.get(e["pad"], false):
				down[e["pad"]] = false
				m.release(int(e["pad"]), float(e["t"]), int(e["pad"]))
			k += 1
		m.advance(t)
		for ev in m.drain_events():
			if ev["kind"] in ["outcome", "wave", "reward_done"]:
				timeline.append({"t": snappedf(t, 0.01), "event": ev})
		if m.battle_enabled:
			peak[0] = maxi(peak[0], m.sim.count_alive(0, BattleSim.Kind.UNIT))
			peak[1] = maxi(peak[1], m.sim.count_alive(1, BattleSim.Kind.UNIT))
	var r := m.result()
	r["policy"] = policy
	r["seed"] = level.seed
	r["peak_live_units"] = peak
	r["song_duration_s"] = duration
	r["timeline"] = timeline
	return r


static func _debug_line(m: Match, t: float, shots: Array, kills: Array) -> void:
	var sim := m.sim
	if sim.defense:
		var orders := {}
		var xs := []
		var tg := 0
		for e in sim.entities:
			if e.alive and e.side == 1 and e.kind == BattleSim.Kind.UNIT:
				var key: String = "%s/%d" % [e.order, e.stage]
				orders[key] = int(orders.get(key, 0)) + 1
				xs.append(snappedf(e.x, 0.1))
				if e.target >= 0:
					tg += 1
		xs.sort()
		var mine := 0
		for e in sim.entities:
			if e.alive and e.side == 0 and e.kind == BattleSim.Kind.UNIT:
				mine += 1
		print("t=%5.1f mine %d enemies %d with_target %d orders %s xs %s" % [t, mine, xs.size(), tg, orders, xs.slice(0, 12)])
		return
	var line := "t=%5.1f" % t
	for side in 2:
		var units := 0
		var with_target := 0
		var in_range := 0
		var moving := 0
		var stuck := 0
		var front := 0.0 if side == 0 else float(sim.width)
		var targets := {}
		for e in sim.entities:
			if not e.alive or e.side != side or e.kind != BattleSim.Kind.UNIT:
				continue
			units += 1
			if side == 0:
				front = maxf(front, e.x)
			else:
				front = minf(front, e.x)
			if e.moving:
				moving += 1
			if e.stuck > 0:
				stuck += 1
			var tg: BattleSim.Ent = sim.get_entity(e.target)
			if tg != null and tg.alive:
				with_target += 1
				targets[tg.role] = int(targets.get(tg.role, 0)) + 1
				var d := e.center().distance_to(tg.center()) - (tg.radius if tg.kind == BattleSim.Kind.BUILDING else 0.0)
				if d <= sim.max_range(e):
					in_range += 1
		var bot: BotAi = sim.bots[side]
		var sq := []
		for s in bot.squads:
			var tg: BattleSim.Ent = sim.get_entity(s.target)
			sq.append("%s/%s n=%d tgt=%s" % [s.type, s.state, s.units.size(), tg.role if tg != null else "-"])
		var air := []
		for e in sim.entities:
			if e.alive and e.side == side and e.kind == BattleSim.Kind.AIRCRAFT:
				air.append("%s%d" % [BattleSim.Air.keys()[e.air].substr(0, 3), e.ammo])
		var bands := [0, 0, 0, 0, 0]
		var worst_building := 100
		for e in sim.entities:
			if e.alive and e.side == side and e.kind == BattleSim.Kind.UNIT:
				bands[clampi(int(e.x / 11.0), 0, 4)] += 1
			if e.alive and e.side != side and e.kind == BattleSim.Kind.BUILDING and e.role != "wall":
				worst_building = mini(worst_building, e.hp * 100 / e.max_hp)
		line += " | S%d units %3d tgt %3d inrange %3d moving %3d front %5.1f shots %4d kills %3d idle %d xbands %s enemyBldgMin %d%% squads %s air %s" % [side, units, with_target, in_range, moving, front, shots[side], kills[side], bot.idle_pool.size(), bands, worst_building, sq, air]
	print(line)


static func _production_summary(m: Match) -> Dictionary:
	var by_slot := {}
	var points := [0, 0, 0]
	var failed := 0
	for e in m.production_log:
		if e.get("result", "") == "queued":
			var slot: String = e["slot_id"]
			by_slot[slot] = int(by_slot.get(slot, 0)) + 1
			points[int(e["point"])] += 1
		else:
			failed += 1
	return {"groups_by_slot": by_slot, "groups_by_point": points, "failed": failed}
