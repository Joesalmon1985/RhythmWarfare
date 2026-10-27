extends SceneTree
## Headless balance harness (acceptance A08, A12): plays a level with a scripted input policy against its authored
## enemy schedule, with no audio and no rendering, and prints the trace.
##
##   godot --headless --path . -s tools/autoplay.gd -- <pack dir> [policy] [enemy_fraction] [seed]
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
	var loaded := LevelLoader.load_pack(pack)
	if loaded["level"] == null:
		push_error("pack rejected: " + str(loaded["errors"]))
		quit(2)
		return
	var level: Level = loaded["level"]
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	if enemy_fraction < 1.0:
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
	var holding: Dictionary = {}  # lane -> end_time
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
				m.press(n["lane"], n["time"], 1)
				if n["type"] == "hold":
					holding[n["lane"]] = n["end_time"]
			next_note += 1
		for lane in holding.keys():
			if t >= holding[lane] + 0.02:
				m.release(lane, holding[lane] + 0.02, 1)
				holding.erase(lane)
		m.advance(t)
		for ev in m.drain_events():
			match ev["kind"]:
				"producer_lost", "pad_lost", "outcome", "stem":
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
	r["enemy_events_used"] = level.enemy_events.size()
	r["timeline"] = timeline
	r["blocked"] = m.sim.stats["blocked"]
	return r


static func _debug_line(m: Match, t: float, shots: Array, kills: Array) -> void:
	var sim := m.sim
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
		line += " | S%d units %3d tgt %3d inrange %3d moving %3d front %5.1f shots %4d kills %3d idle %d squads %s air %s" % [side, units, with_target, in_range, moving, front, shots[side], kills[side], bot.idle_pool.size(), sq, air]
	print(line)
