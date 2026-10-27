extends SceneTree
## Debugging probe: run a scripted match headless and print where every ground unit is at a given song second.
##   godot --headless --path . -s tools/probe.gd -- <pack dir> <policy> <seconds>

const FRAME_S := 1.0 / 60.0


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var pack: String = args[0]
	var policy: String = args[1] if args.size() > 1 else "perfect"
	var at := float(args[2]) if args.size() > 2 else 60.0
	var level: Level = LevelLoader.load_pack(pack)["level"]
	var rng := RandomNumberGenerator.new()
	rng.seed = 1
	var m := Match.new()
	m.setup(level)
	var plan: Array = []
	var prob := 1.0 if policy == "perfect" else float(policy.substr(9))
	for n in level.notes:
		plan.append(rng.randf() < prob)
	var next_note := 0
	var holding := {}
	var t := -1.0
	while m.outcome.is_empty() and t < at:
		t += FRAME_S
		while next_note < level.notes.size() and level.notes[next_note]["time"] <= t:
			var n: Dictionary = level.notes[next_note]
			if plan[next_note]:
				m.press(int(n["button"]), n["time"], 1)
				if n["type"] == "hold":
					holding[int(n["button"])] = n["end_time"]
			next_note += 1
		for b in holding.keys():
			if t >= holding[b] + 0.02:
				m.release(b, holding[b] + 0.02, 1)
				holding.erase(b)
		m.advance(t)
	var sim := m.sim
	print("t=%.1f outcome=%s" % [t, m.outcome])
	for side in 2:
		var grid := {}
		var by_actor := {}
		var orders := {}
		var stuck := 0
		for e in sim.entities:
			if not e.alive or e.side != side or e.kind != BattleSim.Kind.UNIT:
				continue
			var key := Vector2i(int(e.x) / 2, int(e.y) / 2)
			grid[key] = int(grid.get(key, 0)) + 1
			by_actor[e.actor] = int(by_actor.get(e.actor, 0)) + 1
			var o := e.order + ("+tgt" if e.target >= 0 else "") + ("+path" if not e.path.is_empty() else "") + ("+wait" if e.wait_ticks > 0 else "")
			orders[o] = int(orders.get(o, 0)) + 1
			if e.stuck > 5:
				stuck += 1
		print("side %d actors %s orders %s stuck>5: %d" % [side, by_actor, orders, stuck])
		var rows := []
		for y in range(0, sim.height / 2):
			var row := ""
			for x in range(0, (sim.width + 1) / 2):
				var n: int = int(grid.get(Vector2i(x, y), 0))
				row += "." if n == 0 else (str(n) if n < 10 else "#")
			rows.append(row)
		print("\n".join(rows))
	var buildings := []
	for e in sim.entities:
		if e.kind == BattleSim.Kind.BUILDING and e.side == 1 and not e.is_wall:
			buildings.append("%s %d%%%s" % [e.role, e.hp * 100 / e.max_hp, "" if e.alive else " DEAD"])
	print("enemy buildings: ", ", ".join(buildings))
	var walls := 0
	var walls_alive := 0
	for e in sim.entities:
		if e.kind == BattleSim.Kind.BUILDING and e.side == 1 and e.is_wall:
			walls += 1
			if e.alive:
				walls_alive += 1
	print("enemy walls alive %d/%d" % [walls_alive, walls])
	# the most forward player units in detail
	var fwd := []
	for e in sim.entities:
		if e.alive and e.side == 0 and e.kind == BattleSim.Kind.UNIT:
			fwd.append(e)
	fwd.sort_custom(func(a, b): return a.x > b.x)
	for e in fwd.slice(0, 14):
		var tg: BattleSim.Ent = sim.get_entity(e.target)
		var wp: Vector2 = e.path[e.path_index] if not e.path.is_empty() and e.path_index < e.path.size() else Vector2(-1, -1)
		print("  %s at (%.1f,%.1f) hp %d/%d order %s -> %s target %s path %d/%d next %s goal %s stuck %d wait %d moving %s heading %.2f" % [
			e.actor, e.x, e.y, e.hp, e.max_hp, e.order, e.order_pos, (tg.role + "@(%.1f,%.1f)" % [tg.x, tg.y]) if tg != null else "-",
			e.path_index, e.path.size(), wp, e.path_goal, e.stuck, e.wait_ticks, e.moving, e.heading])
	# blocked cells around the enemy's outer wall
	for y in sim.height:
		var row := ""
		for x in range(34, 46):
			var id: int = int(sim._blocked.get(Vector2i(x, y), -2))
			var b: BattleSim.Ent = sim.get_entity(id)
			row += "." if id == -2 else ("T" if id == -1 else (b.role.substr(0, 1) if b != null and b.alive else "x"))
		print("  x34-45 y%02d %s  foot_solid %s track_solid %s" % [y, row, sim._astar_foot.is_point_solid(Vector2i(38, y)), sim._astar_track.is_point_solid(Vector2i(38, y))])
	quit(0)
