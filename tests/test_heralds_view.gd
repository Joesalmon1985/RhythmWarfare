extends TestCase
## The quest entrances are in the player's picture (docs/art/HERALDS.md, the visibility rule): for every scene with a herald, the scripted run is played from the Warehouse's
## first beat to that scene (perfect play, the flags that put every entrance on offer), its journey replayed on the real rail camera (StoryPlayer), and at every sample of the
## opening (beats OPEN_FROM to OPEN_TO of the scene) and of the route window (beats WIN_FROM to WIN_TO) the screen rectangles of the entrance (its ground up to the top of its
## mark) and of its herald (feet to head) are projected into the stage strip of a 1280 x 720 window (the narrowest picture we ship: a 20:9 phone shows more at the sides) and must
## lie inside the visible picture, the HUD's corners left out, for at least SHARE of the samples. An early-window entrance (the Floor wizard) is on offer only in blocks 0 and 1:
## its route window is the opening. The old camera (no heralds' look, the star and the radio behind the standpoint) fails this.

const VIEW := Vector2(1280.0, 460.0)  # the stage strip of a 1280 x 720 window: the pads are below it
const HUD_BOXES := [Rect2(0, 0, 345, 100), Rect2(1180, 0, 100, 70)]  # the energy and progress bars, the pause button
const OPEN_FROM := 4.0
const OPEN_TO := 12.0
const WIN_FROM := 49.0
const WIN_TO := 60.0
const SHARE := 0.8
const IN_FRAME := 0.75  # this much of a rectangle's area inside the visible picture counts as in frame
const FLAGS := {"wh_saw_floor": true, "wh_vip_pass": true}
## scene -> the scenes the run passes through to get there from the Warehouse's first scene
const ROUTES := {"warehouse": [], "warehouse.balcony": ["warehouse.balcony"], "warehouse.booth": ["warehouse.balcony", "warehouse.booth"], "warehouse.bar": ["warehouse.bar"],
	"warehouse.chill": ["warehouse.bar", "warehouse.chill"],
	# N2.4 Alien Spaceship (the mothership): from the Warehouse's exit, then the hub's own side scenes
	"mothership": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership"],
	"mothership.gallery": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery"],
	"mothership.reactor": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.reactor"],
	"mothership.bridge": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge"],
	}


## One scripted run to `target`: {player: StoryPlayer, t0: the target phase's downbeat, beat, hotspots: the target's herald entrances [{id, herald, early}]}.
func _play_to(data: RunData, target: String, looks := true) -> Dictionary:
	var e := RunEngine.new(data)
	e.hotspots = RunHotspots.new(data, FLAGS.duplicate(), {})
	e.begin("warehouse")
	var j := RunJourney.new(data)
	j.look_heralds = looks
	var maps := {}
	j.face_fn = func(node_id: String, _place: String) -> Array:  # the run scene's window turn (RunPlay._window_face), with the map alone
		var mid := str(data.nodes[node_id]["map"])
		if not maps.has(mid):
			maps[mid] = StoryMap.load_chapter(mid, false)
		var pts: Array = []
		for h in e.hotspots.shown(3, true):
			if RunHotspots.window_of(h) != "final":
				continue
			var r := HotspotView.resolve(h["anchor"], maps[mid], {})
			if bool(r["ok"]):
				var p: Vector3 = r["pos"]
				pts.append([p.x, p.z, 1.0 if bool(h["default"]) else 0.0, p.y])
		return pts
	var plan: Array = (ROUTES[target] as Array).duplicate()
	var actions: Array = []
	var t := -0.5
	var next_i := 0
	var held: Array = []
	var chosen := {}
	var door := {}
	var t0 := -1.0
	var phase_n := -1
	var entrances: Array = []
	while t < 40.0 * 64.0 * e.beat_s and not e.over:
		for ev in e.update(t):
			if str(ev["kind"]) in ["phase_start", "block_result", "lap_start"]:
				actions.append_array(j.on_event(ev, e))
			if str(ev["kind"]) == "phase_start" and str(ev["node"]) == target and t0 < 0.0:
				t0 = float(ev["t"])
				phase_n = int(ev["phase"])
				for h in e.hotspots.staged(0):
					if (h as Dictionary).has("herald"):
						entrances.append({"id": str(h["id"]), "herald": h["herald"], "early": RunHotspots.window_of(h) == "early"})
		while next_i < e.level.notes.size() and float(e.level.notes[next_i]["time"]) <= t:
			var n: Dictionary = e.level.notes[next_i]
			e.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
			held.append({"pad": int(n["pad"]), "up": float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.06})
			next_i += 1
		for hd in held.duplicate():
			if float(hd["up"]) <= t:
				e.release(int(hd["pad"]), float(hd["up"]), int(hd["pad"]))
				held.erase(hd)
		if t0 >= 0.0 and t > t0 + 64.0 * e.beat_s:
			break
		if e.window_open and not chosen.has(e.phase_n) and e.phase_beat_at(t) > 52.0 and not plan.is_empty() and e.node_id != target:
			chosen[e.phase_n] = true
			e.choose(str(plan.pop_front()))
		if e.window_open and not door.has(e.phase_n) and e.phase_beat_at(t) >= 61.0:
			door[e.phase_n] = true
			var to := e.selected_route()
			if data.nodes.has(to) and str(data.nodes[to]["world"]) == str(data.nodes[e.node_id]["world"]) and to != e.node_id:
				actions.append_array(j.leave_walk(e.t_of(61.0), to, e))
		t += 1.0 / 30.0
	var p := StoryPlayer.new()
	p.setup(StoryMap.load_chapter(str(data.nodes[target]["map"]), false), float(data.cfg["timing"]["bpm"]))
	for a in actions:
		if str(a["world"]) == str(data.nodes[target]["map"]):
			p.apply_action(a)
	return {"player": p, "t0": t0, "beat": e.beat_s, "entrances": entrances, "phase": phase_n}


## How much of `r` lies in the visible picture (the strip, the HUD's corners left out), 0 to 1.
static func visible_share(r: Rect2) -> float:
	if r.size.x <= 0.0 or r.size.y <= 0.0:
		return 0.0
	var inside := r.intersection(Rect2(Vector2.ZERO, VIEW))
	var area := inside.get_area()
	for b in HUD_BOXES:
		area -= inside.intersection(b).get_area()
	return maxf(area, 0.0) / r.get_area()


## The screen rectangle of an upright thing `w_m` wide from height y0 to y1 at ground point g; an empty rect when it is behind the camera.
static func rect_of(g: Vector2, y0: float, y1: float, w_m: float, pose: Dictionary) -> Rect2:
	var lo := StoryProjector.project(Vector3(g.x, y0, g.y), pose, VIEW)
	var hi := StoryProjector.project(Vector3(g.x, y1, g.y), pose, VIEW)
	if float(lo["depth"]) < StoryProjector.NEAR or float(hi["depth"]) < StoryProjector.NEAR:
		return Rect2()
	var half := 0.5 * w_m * float(lo["scale"])
	var a: Vector2 = lo["screen"]
	var b: Vector2 = hi["screen"]
	return Rect2(minf(a.x, b.x) - half, minf(a.y, b.y), absf(a.x - b.x) + 2.0 * half, absf(a.y - b.y))


## {entrance, herald}: the share of samples in [from_b, to_b] beats of the scene in which each is in frame.
func _shares(run: Dictionary, ent: Dictionary, from_b: float, to_b: float) -> Dictionary:
	var p: StoryPlayer = run["player"]
	var b: Dictionary = ent["herald"]
	var pts := StoryHeralds.look_points(b, p.map)  # [entrance, mark top, herald knees, herald head]
	var n := 0
	var e_in := 0
	var h_in := 0
	var beat := from_b
	while beat <= to_b + 1.0e-6:
		var pose := p.pose_at(float(run["t0"]) + beat * float(run["beat"]))
		n += 1
		if OS.get_environment("RW_HERALD_VIEW_DEBUG") != "" and fposmod(beat, 4.0) < 0.01:  # (a trace for whoever places an entrance)
			var e0: Array = pts[0]
			print("    beat %5.1f cam (%.2f, %.2f) yaw %6.1f pitch %5.1f  entrance %s  herald %s" % [beat, pose["pos"].x, pose["pos"].y, pose["yaw"], pose["pitch"],
				rect_of(Vector2(e0[0], e0[1]), float(e0[3]), float((pts[1] as Array)[3]), 0.6, pose), rect_of(Vector2(pts[2][0], pts[2][1]), float(pts[2][3]) - StoryHeralds.LOOK_KNEE, float(pts[3][3]), 0.7, pose) if pts.size() >= 4 else "-"])
		var ep: Array = pts[0]
		if visible_share(rect_of(Vector2(ep[0], ep[1]), float(ep[3]), float((pts[1] as Array)[3]), 0.6, pose)) >= IN_FRAME:
			e_in += 1
		if pts.size() >= 4:
			var hp: Array = pts[2]
			if visible_share(rect_of(Vector2(hp[0], hp[1]), float(hp[3]) - StoryHeralds.LOOK_KNEE, float((pts[3] as Array)[3]), 0.7, pose)) >= IN_FRAME:  # (feet to head)
				h_in += 1
		else:
			h_in += 1
		beat += 0.25
	return {"entrance": float(e_in) / float(n), "herald": float(h_in) / float(n)}


func _check_all(looks: bool) -> Dictionary:
	var data := RunData.load_default()
	var out := {}
	for scene in ROUTES:
		var with_herald := false
		for h in data.hotspots.get(scene, []):
			with_herald = with_herald or (h as Dictionary).has("herald")
		if not with_herald:
			continue
		var run := _play_to(data, scene, looks)
		for ent in run["entrances"]:
			var o := _shares(run, ent, OPEN_FROM, OPEN_TO)
			var w := o if bool(ent["early"]) else _shares(run, ent, WIN_FROM, WIN_TO)
			out[str(ent["id"])] = {"open": o, "window": w, "scene": scene, "t0": run["t0"]}
	return out


func test_every_quest_entrance_and_its_herald_are_in_the_picture_in_the_opening_and_the_route_window() -> void:
	var res := _check_all(true)
	var data := RunData.load_default()
	var ids := []
	for scene in data.hotspots:
		for h in data.hotspots[scene]:
			if (h as Dictionary).has("herald") and ROUTES.has(str(h["scene"])):
				ids.append(str(h["id"]))
	for id in ids:
		assert_true(res.has(id), "%s: on offer in the scripted run (its flags set)" % id)
	for id in res:
		var r: Dictionary = res[id]
		print("  herald view %-28s opening entrance %3d%% herald %3d%%   window entrance %3d%% herald %3d%%" % [id, roundi(100.0 * float(r["open"]["entrance"])), roundi(100.0 * float(r["open"]["herald"])),
			roundi(100.0 * float(r["window"]["entrance"])), roundi(100.0 * float(r["window"]["herald"]))])
		for when in ["open", "window"]:
			for what in ["entrance", "herald"]:
				assert_true(float(r[when][what]) >= SHARE, "%s: the %s is in the picture %.0f%% of the %s (needs %.0f%%)" % [id, what, 100.0 * float(r[when][what]), "opening" if when == "open" else "route window", 100.0 * SHARE])


func test_without_the_heralds_look_the_opening_misses_them() -> void:
	var res := _check_all(false)
	var short := 0
	for id in res:
		var r: Dictionary = res[id]
		if float(r["open"]["entrance"]) < SHARE or float(r["open"]["herald"]) < SHARE:
			short += 1
	assert_true(short >= 2, "the rail's own camera leaves at least two entrances out of the opening (%d): the look is what brings them in" % short)


func test_the_look_is_data_only_one_face_look_a_staged_herald_never_a_move() -> void:
	var data := RunData.load_default()
	var e := RunEngine.new(data)
	e.hotspots = RunHotspots.new(data, FLAGS.duplicate(), {})
	e.begin("warehouse.bar")
	var j := RunJourney.new(data)
	var acts: Array = []
	var t := 0.0
	while acts.is_empty() and t < 5.0:
		for ev in e.update(t):
			acts.append_array(j.on_event(ev, e))
		t += 0.05
	var faces := acts.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_look" and (a["args"] as Dictionary).has("face"))
	assert_eq(faces.size(), 1, "one look for the bar's one entrance on offer (the ember)")
	var glances := acts.filter(func(a: Dictionary) -> bool: return str(a["action"]) == "player_look" and not (a["args"] as Dictionary).has("face"))
	assert_eq(glances.size(), 0, "the block's own glance is left out while the look holds the entrance")
	for a in acts:
		assert_true(str(a["action"]) != "player_move" or not (a["args"] as Dictionary).has("face"), "a look, never a move")
	var off := RunHotspots.new(data, {}, {})
	off.begin_scene("warehouse.bar", 60.0)
	e.hotspots = off
	assert_eq(j.staged_heralds("warehouse.bar", e), [], "without the VIP pass the ember is not on offer: no look")
