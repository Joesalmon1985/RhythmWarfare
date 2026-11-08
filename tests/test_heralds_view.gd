extends TestCase
## The quest entrances are in the player's picture (docs/art/HERALDS.md, the visibility rule): for every scene with a herald, the scripted run is played from the Warehouse's
## first beat to that scene (perfect play, the flags that put every entrance on offer), its journey replayed on the real rail camera (StoryPlayer), and at every sample of the
## opening (beats OPEN_FROM to OPEN_TO of the scene) and of the route window (beats WIN_FROM to WIN_TO) the screen rectangles of the entrance (its ground up to the top of its
## mark) and of its herald (feet to head) are projected into the stage strip of a 1280 x 720 window (the narrowest picture we ship: a 20:9 phone shows more at the sides) and must
## lie inside the visible picture, the HUD's corners left out, for at least SHARE of the samples. An early-window entrance (the Floor wizard) is on offer only in blocks 0 and 1:
## its route window is the opening. The old camera (no heralds' look, the star and the radio behind the standpoint) fails this.
## A sample counts only when nothing stands between the eye and the thing (`occluder`): a ray from the camera to the entrance's mark and one to the herald's head are cast against the
## map's walls, floors and ceilings as tools/art/camera_clearance_check.gd casts them, and against the map's occluders (the cut-outs drawn over the crowd: the card table); the dancers
## themselves are not seen (they move). A scene's way back to its hub (`<scene>.to_hub`, the shared wiring step) is in the picture, unoccluded, for RETURN_SHARE of the route window
## while the entrances keep theirs (the window look weighs the entrances more than the way back: RunJourney.WINDOW_ENTRANCE_W).

const VIEW := Vector2(1280.0, 460.0)  # the stage strip of a 1280 x 720 window: the pads are below it
const HUD_BOXES := [Rect2(0, 0, 345, 100), Rect2(1180, 0, 100, 70)]  # the energy and progress bars, the pause button
const OPEN_FROM := 4.0
const OPEN_TO := 12.0
const WIN_FROM := 49.0
const WIN_TO := 60.0
const SHARE := 0.8
const IN_FRAME := 0.75  # this much of a rectangle's area inside the visible picture counts as in frame
const FLAGS := {"wh_saw_floor": true, "wh_vip_pass": true}
const RETURN_SHARE := 0.5
## The entrances ("<hotspot id>:open|window") that are in the picture but behind a wall or an occluder for more than a fifth of the samples (the wall test's findings on the merged
## tree, 7 November 2026: placement work for their location packages; docs/parallel-development/RUN_LOG.md lists them). A new one fails; one fixed comes off the list.
const KNOWN_HIDDEN := [
	"hospital.enter_bassment:open", "hospital.enter_gospel:open", "mothership.enter_ember:window", "mothership.gallery.enter_bassment:open",
	"mothership.reactor.enter_gospel:open", "underworld.court.enter_bassment:open", "underworld.enter_bassment:window", "ward.art.enter_bassment:open",
	"ward.corridor.enter_squadron:open", "ward.courtyard.enter_ember:open", "ward.dorm.enter_gospel:open", "ward_late.dorm.enter_gospel:open",
	"ward_late.treat.enter_bassment:open", "warehouse.booth.radio:open", "warehouse.enter_bassment:window", "warehouse.enter_ember:window", "warehouse.enter_gospel:window",
	"warehouse.enter_squadron:window"]
## The ways back to the hub under RETURN_SHARE of the route window (placement work: tools/run/hub_door_spots.gd searches a spot).
const KNOWN_BACK_UNSEEN := [
	"back:mothership.reactor.to_hub", "back:underworld.court.to_hub", "back:ward.art.to_hub", "back:ward.courtyard.to_hub", "back:warehouse.chill.to_hub"]
const DOOR_H := 2.4
const OCCLUDER_SOLID := 0.5  # an occluder's cut-out is solid over the lower half of its height (a table and the players at it; the sprite's top is mostly air)  # the way back's door, from its foot (its doorway waypoint) to its lintel
const CC := preload("res://tools/art/camera_clearance_check.gd")
## scene -> the scenes the run passes through to get there from the Warehouse's first scene
const ROUTES := {"warehouse": [], "warehouse.balcony": ["warehouse.balcony"], "warehouse.booth": ["warehouse.balcony", "warehouse.booth"], "warehouse.bar": ["warehouse.bar"],
	"warehouse.chill": ["warehouse.bar", "warehouse.chill"],
	# N2.4 Hell (underworld): out of the Warehouse by the exit's east door, then the arena and its side scenes
	"underworld": ["warehouse.bar", "warehouse.booth", "warehouse.exit", "underworld"],
	"underworld.court": ["warehouse.bar", "warehouse.booth", "warehouse.exit", "underworld", "underworld.court"],
	"underworld.furnace": ["warehouse.bar", "warehouse.booth", "warehouse.exit", "underworld", "underworld.furnace"],
	"underworld.pit": ["warehouse.bar", "warehouse.booth", "warehouse.exit", "underworld", "underworld.court", "underworld.pit"],
	# N2.4 Alien Spaceship (the mothership): from the Warehouse's exit, then the hub's own side scenes
	"mothership": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership"],
	"mothership.gallery": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery"],
	"mothership.reactor": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.reactor"],
	"mothership.bridge": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge"],
	# Mental Hospital (N2.4): the hub and the side scenes of the ward and ward_late worlds, from the Warehouse through the mothership (and the hospital)
	"ward": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "ward"],
	"ward.art": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "ward", "ward.art"],
	"ward.dorm": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "ward", "ward.dorm"],
	"ward.corridor": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "ward", "ward.art", "ward.corridor"],
	"ward.courtyard": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "ward", "ward.art", "ward.corridor", "ward.courtyard"],
	"ward_late.treat": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital", "hospital.corridor", "hospital.dayroom", "hospital.garden", "hospital.exit", "ward_late", "ward_late.treat"],
	"ward_late.dorm": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital", "hospital.corridor", "hospital.dayroom", "hospital.garden", "hospital.exit", "ward_late", "ward_late.dorm"],
	# N2.4 Hospital Ward (hospital, hospital_late): by the Mothership's airlock, then the ward and its side scenes
	"hospital": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital"],
	"hospital.dayroom": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital", "hospital.corridor", "hospital.dayroom"],
	"hospital.cafeteria": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital", "hospital.corridor", "hospital.cafeteria"],
	"hospital.garden": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital", "hospital.corridor", "hospital.dayroom", "hospital.garden"],
	"hospital_late.cafe": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital", "hospital.corridor", "hospital.dayroom", "hospital.garden", "hospital.exit", "hospital_late", "hospital_late.cafe"],
	"hospital_late.quiet": ["warehouse.bar", "warehouse.chill", "warehouse.exit", "mothership", "mothership.gallery", "mothership.bridge", "mothership.exit", "hospital", "hospital.corridor", "hospital.dayroom", "hospital.garden", "hospital.exit", "hospital_late", "hospital_late.quiet"]}


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
		return RunJourney.window_points(e.hotspots.shown(3, true), maps[mid])
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


## What stands between the eye at `pose` and the point (g, y) of map `m`: "" nothing, else a wall's or an occluder's description. The wall ray is camera_clearance_check.gd's (walls, steps,
## lintels, floors and ceilings); an occluder is a cut-out `width` wide standing upright at its foot, solid OCCLUDER_SOLID of its `height` above its sector's floor.
static func occluder(m: StoryMap, pose: Dictionary, g: Vector2, y: float) -> String:
	var cam: Vector3 = pose["cam"]
	var c2 := Vector2(cam.x, cam.z)
	var rel := g - c2
	var d := rel.length()
	if d < 0.3:
		return ""
	var dir := rel / d
	var slope := (y - cam.y) / d
	var r: Dictionary = CC.cast(m, c2, CC.sector_of(m, c2, str(pose.get("sector", ""))), dir, cam.y, slope)
	if float(r["s"]) < d - 0.35:
		return str(r["what"])
	for o in m.occluders:
		var at: Vector2 = o["at"]
		var t := (at - c2).dot(dir)
		if t < 0.3 or t > d - 0.3:
			continue
		var side := absf((at - c2).cross(dir))
		var fl := float(m.sector(str(o.get("sector", ""))).get("floor", 0.0)) if str(o.get("sector", "")) != "" else 0.0
		if side < 0.5 * float(o["width"]) and cam.y + slope * t < fl + OCCLUDER_SOLID * float(o["height"]):
			return "occluder %s" % o["id"]
	return ""


## {entrance, herald}: the share of samples in [from_b, to_b] beats of the scene in which each is in frame and not hidden (occluder).
func _shares(run: Dictionary, ent: Dictionary, from_b: float, to_b: float) -> Dictionary:
	var p: StoryPlayer = run["player"]
	var b: Dictionary = ent["herald"]
	var pts := StoryHeralds.look_points(b, p.map)  # [entrance, mark top, herald knees, herald head]
	var n := 0
	var e_in := 0
	var h_in := 0
	var hidden := {}
	var beat := from_b
	while beat <= to_b + 1.0e-6:
		var pose := p.pose_at(float(run["t0"]) + beat * float(run["beat"]))
		n += 1
		if OS.get_environment("RW_HERALD_VIEW_DEBUG") != "" and fposmod(beat, 4.0) < 0.01:  # (a trace for whoever places an entrance)
			var e0: Array = pts[0]
			print("    beat %5.1f cam (%.2f, %.2f) yaw %6.1f pitch %5.1f  entrance %s  herald %s" % [beat, pose["pos"].x, pose["pos"].y, pose["yaw"], pose["pitch"],
				rect_of(Vector2(e0[0], e0[1]), float(e0[3]), float((pts[1] as Array)[3]), 0.6, pose), rect_of(Vector2(pts[2][0], pts[2][1]), float(pts[2][3]) - StoryHeralds.LOOK_KNEE, float(pts[3][3]), 0.7, pose) if pts.size() >= 4 else "-"])
		var ep: Array = pts[0]
		var mk: Array = pts[1]
		if visible_share(rect_of(Vector2(ep[0], ep[1]), float(ep[3]), float(mk[3]), 0.6, pose)) >= IN_FRAME:
			var why := occluder(p.map, pose, Vector2(mk[0], mk[1]), float(mk[3]))
			if why != "" and occluder(p.map, pose, Vector2(ep[0], ep[1]), 0.5 * (float(ep[3]) + float(mk[3]))) == "":
				why = ""  # (the mark over a doorway may be under a lintel: the entrance's middle seen is enough)
			if why == "":
				e_in += 1
			else:
				hidden[why] = true
		if pts.size() >= 4:
			var hp: Array = pts[2]
			var hd: Array = pts[3]
			if visible_share(rect_of(Vector2(hp[0], hp[1]), float(hp[3]) - StoryHeralds.LOOK_KNEE, float(hd[3]), 0.7, pose)) >= IN_FRAME:  # (feet to head)
				var why := occluder(p.map, pose, Vector2(hd[0], hd[1]), float(hd[3]))
				if why != "" and occluder(p.map, pose, Vector2(hd[0], hd[1]), float(hd[3]) - 0.45) == "":
					why = ""  # (the head or the chest seen)
				if why == "":
					h_in += 1
				else:
					hidden["herald: " + why] = true
		else:
			h_in += 1
		beat += 0.25
	return {"entrance": float(e_in) / float(n), "herald": float(h_in) / float(n), "hidden": hidden.keys()}


## The share of samples in [from_b, to_b] in which a door standing at ground point g (DOOR_H tall, 1.2 m wide) is in frame and not hidden.
func _door_share(run: Dictionary, g: Vector2, y0: float, from_b: float, to_b: float) -> float:
	var p: StoryPlayer = run["player"]
	var n := 0
	var k := 0
	var beat := from_b
	while beat <= to_b + 1.0e-6:
		var pose := p.pose_at(float(run["t0"]) + beat * float(run["beat"]))
		n += 1
		if visible_share(rect_of(g, y0, y0 + DOOR_H, 1.2, pose)) >= IN_FRAME and occluder(p.map, pose, g, y0 + 0.5 * DOOR_H) == "":
			k += 1
		beat += 0.25
	return float(k) / float(n)


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
		for h in data.hotspots.get(scene, []):  # the scene's way back to its hub (RETURN_SHARE of the route window)
			if RunJourney.is_way_back(h):
				var r := HotspotView.resolve(h["anchor"], (run["player"] as StoryPlayer).map, {})
				if bool(r["ok"]):
					var rp: Vector3 = r["pos"]
					out["back:" + str(h["id"])] = {"back": _door_share(run, Vector2(rp.x, rp.z), rp.y, WIN_FROM, WIN_TO), "scene": scene}
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
	var hidden: Array = []
	var backs_short: Array = []
	for id in ids:
		assert_true(res.has(id), "%s: on offer in the scripted run (its flags set)" % id)
	for id in res:
		var r: Dictionary = res[id]
		if r.has("back"):
			print("  herald view %-34s way back in the route window %3d%%" % [id, roundi(100.0 * float(r["back"]))])
			if float(r["back"]) < RETURN_SHARE:
				backs_short.append(id)
			continue
		print("  herald view %-28s opening entrance %3d%% herald %3d%%   window entrance %3d%% herald %3d%%" % [id, roundi(100.0 * float(r["open"]["entrance"])), roundi(100.0 * float(r["open"]["herald"])),
			roundi(100.0 * float(r["window"]["entrance"])), roundi(100.0 * float(r["window"]["herald"]))])
		for when in ["open", "window"]:
			for what in ["entrance", "herald"]:
				var ok := float(r[when][what]) >= SHARE
				var why := "%s: the %s is in the picture %.0f%% of the %s (needs %.0f%%)%s" % [id, what, 100.0 * float(r[when][what]), "opening" if when == "open" else "route window", 100.0 * SHARE,
					"" if (r[when]["hidden"] as Array).is_empty() else "; hidden by " + ", ".join(PackedStringArray(r[when]["hidden"]))]
				if not ok and not (r[when]["hidden"] as Array).is_empty():  # in the picture but behind a wall or an occluder: a hidden gate, pinned below
					print("  hidden %s" % why)
					if not hidden.has("%s:%s" % [id, when]):
						hidden.append("%s:%s" % [id, when])
					continue
				assert_true(ok, why)
	hidden.sort()
	var want: Array = KNOWN_HIDDEN.duplicate()
	want.sort()
	assert_eq(hidden, want, "the entrances a wall or an occluder hides for more than a fifth of their samples are exactly the known ones (a new one is a hidden gate; one fixed comes off the list)")
	backs_short.sort()
	var want_b: Array = KNOWN_BACK_UNSEEN.duplicate()
	want_b.sort()
	assert_eq(backs_short, want_b, "the ways back under RETURN_SHARE of the route window are exactly the known ones")


func test_without_the_heralds_look_the_opening_misses_them() -> void:
	var res := _check_all(false)
	var short := 0
	for id in res:
		var r: Dictionary = res[id]
		if r.has("back"):
			continue
		if float(r["open"]["entrance"]) < SHARE or float(r["open"]["herald"]) < SHARE:
			short += 1
	assert_true(short >= 2, "the rail's own camera leaves at least two entrances out of the opening (%d): the look is what brings them in" % short)


## The occlusion rays themselves: a wall between the eye and the entrance hides it, an open room does not, a cut-out in front hides what is behind it up to its height.
func test_a_wall_or_an_occluder_between_the_eye_and_an_entrance_hides_it() -> void:
	var m := StoryMap.from_dict({"id": "box", "start": "a", "sectors": [
		{"id": "a", "polygon": [[-5, -10], [5, -10], [5, 0], [-5, 0]], "floor": 0, "ceiling": 3},
		{"id": "b", "polygon": [[-5, 0], [5, 0], [5, 10], [-5, 10]], "floor": 0, "ceiling": 3}],
		"walls": [{"sector": "a", "from": [5, 0], "to": [1, 0], "portal": "b"}],
		"waypoints": [{"id": "a", "at": [0, -5], "yaw": 180, "sector": "a"}],
		"textures": {"t": "t.png"}, "occluders": [{"id": "crate", "sprite": "t", "at": [3, -2], "width": 1.0, "height": 1.2}]})
	assert_eq(m.errors, [], "the test map builds")
	var pose := {"cam": Vector3(0, 1.6, -5), "yaw": 180.0, "sector": "a"}
	assert_eq(occluder(m, pose, Vector2(0, -1), 1.0), "", "an entrance in the same open room is seen")
	assert_true(occluder(m, pose, Vector2(-7, -2), 1.0) != "", "an entrance beyond the room's side wall is hidden")
	assert_eq(occluder(m, pose, Vector2(3, 5), 1.5), "", "one seen through the opening is not")
	assert_true(occluder(m, pose, Vector2(4.5, -0.5), 0.0).begins_with("occluder"), "a low point behind the crate is hidden")
	assert_eq(occluder(m, pose, Vector2(3.5, -1.5), 2.8), "", "a high point just past the crate shows over it")


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


func test_a_later_lap_keeps_its_blocks_own_glances() -> void:
	# the heralds' look is the scene's opening: a lap after the first (a track scene plays several) has no herald look, so its blocks keep the rail's glances (walk_run.sh: every block a glance)
	var data := RunData.load_default()
	var e := RunEngine.new(data)
	e.hotspots = RunHotspots.new(data, FLAGS.duplicate(), {})
	e.begin("warehouse.bar")
	var j := RunJourney.new(data)
	var t := 0.0
	var started := false
	while not started and t < 5.0:
		for ev in e.update(t):
			j.on_event(ev, e)
			started = started or str(ev["kind"]) == "phase_start"
		t += 0.05
	assert_true(j._herald_blocks.has(0), "the opening's herald look takes block 0's glance (the ember on offer)")
	var glance := [{"t0": 1.0, "action": "player_look", "args": {"by": 10.0, "pitch": 0.0, "bars": 2.0}}]
	assert_eq(j._without_glance(glance, 0).size(), 0, "in the opening the herald look holds the block")
	j.on_event({"kind": "lap_start", "t": t, "phase": 2, "node": "warehouse.bar", "lap": 2, "laps": 3}, e)
	assert_true(j._herald_blocks.is_empty(), "a new lap has no herald look")
	assert_eq(j._without_glance(glance, 0).size(), 1, "so a later lap's block keeps its own glance")
