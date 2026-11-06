extends RefCounted
## Records a few ordinary runs on the virtual clock, event by event and cue by cue, as stable text lines (tests/test_run_tracks_safety.gd).

## The recorded runs: name -> lines (one per event, then one per cue), each a stable JSON text.
static func record_all() -> Dictionary:
	var out := {}
	var main := RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, 7)
	out["main_misses"] = _record(main, "warehouse", 6, -1, false)
	out["main_second_route"] = _record(main, "warehouse", 5, 1, false)
	out["main_held"] = _record(main, "warehouse.bar", 3, -1, true)
	var gospel := RunData.load_path("gospel", 7)
	out["gospel_laps"] = _record(gospel, gospel.start_node(), 3, -1, false)
	return out


## One run: a scripted player who hits every cue except one in four (by its index), plays `scenes` scenes, picks route `pick` (-1: the defaults) in the window and, with `held`, holds the run
## (as a minigame does) for the whole of its second scene.
static func _record(d: RunData, start: String, scenes: int, pick: int, held: bool) -> Array:
	var e := RunEngine.new(d)
	e.hotspots = RunHotspots.new(d, {}, {})
	e.begin(start)
	var lines: Array = []
	var t := -0.5
	var done := {}
	var picked := -1
	var guard := 0
	while e.scene_index() <= scenes and not e.over and e.away == "" and guard < 200000:
		guard += 1
		e.hold = held and e.scene_index() == 2
		if pick >= 0 and e.window_open and picked != e.phase_n:
			picked = e.phase_n
			var opts := e.options()
			if opts.size() > pick:
				e.choose(str(opts[pick]["to"]))
		for ev in e.update(t):
			lines.append(_line(ev))
		for i in e.level.notes.size():
			var n: Dictionary = e.level.notes[i]
			if done.has(i) or i % 4 == 3:
				continue
			if float(n["time"]) <= t and not done.has(i):
				e.press(int(n["pad"]), float(n["time"]))
				done[i] = true
				if n["type"] == "hold":
					e.release(int(n["pad"]), float(n["end_time"]))
		t += 1.0 / 30.0
	for n in e.level.notes:
		lines.append(_line({"note": n["id"], "tick": n["tick"], "dur": n["duration_ticks"], "time": n["time"], "end_time": n["end_time"], "pad": n["pad"], "family": n["family"],
			"type": n["type"], "phase": n["phase"], "block": n["block"], "voice": n["voice"]}))
	lines.append(_line({"energy": e.energy, "phase_n": e.phase_n, "node": e.node_id}))
	return lines


## A stable text of an event: keys sorted, floats to 1e-9 (the comparison is of song times, not of the last bit).
static func _line(v: Variant) -> String:
	return JSON.stringify(_round(v), "", true)


static func _round(v: Variant) -> Variant:
	match typeof(v):
		TYPE_FLOAT:
			return snappedf(float(v), 1e-9)
		TYPE_DICTIONARY:
			var o := {}
			for k in (v as Dictionary):
				o[k] = _round(v[k])
			return o
		TYPE_ARRAY:
			return (v as Array).map(func(x: Variant) -> Variant: return _round(x))
	return v
