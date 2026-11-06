## (no class_name: tools/art/camera_clearance.gd and tests/test_camera_clearance.gd load it by path)
extends RefCounted
## Camera clearance (docs/art/VISUAL_AUDIT.md F5 and F16, package A5): does the run camera ever stare into a wall from arm's length?
##
## The check itself (pure functions); the runner is tools/art/camera_clearance.gd:
##     bash tools/dev/godot.sh --headless --path . -s tools/art/camera_clearance.gd -- [--step 0.5] [--only <regex on scene id>] [--doc before|after] [--dump file.csv]
##
## For every scene of the main run and of the three paths (gospel, squadron, ember), and for every way the player comes into it, the scene's journey is played on the real
## rail camera (RunEngine + RunJourney + StoryPlayer, the perfect bot and the default exit, like tests/test_heralds_view.gd and the audit's captures), then the camera pose is
## sampled every `step` beats over the whole scene (every lap) and a row of rays across the stage strip is cast against the map (walls, floor and ceiling steps at portals,
## floors and ceilings). The entries of a scene ("how the player comes in"):
##   direct   the scene started on its own (RW_RUN_START: what the audit's frames show; the run's first scene)
##   arrival  stepping in from another world: the passage window opens on the arrival pose (rail.arrive, then the walk home)  (F16)
##   door     a path inside the world: the door walk from the place where the previous scene's rail ends (its top place), sampled from the moment the walk starts
## A pose FAILS when the centre of the picture is nearer than CENTRE_M **and** more than FRAME_SHARE of the picture's width is nearer than FRAME_M (camera depth, the
## distance along the view axis, which sets how much a wall's texels are magnified). Thresholds and why: docs/art/CAMERA_CLEARANCE.md. A doorway the camera is walking
## through (moving, within TRANSIT_M of the opening it crosses) is not judged: the jambs pass by in a beat.
## Prints a table of the failing poses (scene, entry, beat range, pose kind, distances, the wall); --doc writes it into docs/art/CAMERA_CLEARANCE.md between its markers.
## Exits 1 when any pose fails. tests/test_camera_clearance.gd runs the same check (check_all) at one sample a beat.

const CENTRE_M := 2.5  # the centre of the picture nearer than this ...
const FRAME_M := 2.5  # ... and more than FRAME_SHARE of its width nearer than this: the frame is a wall
const FRAME_SHARE := 0.5
const FACE_COS := 0.5  # a wall counts only when it faces the eye within 60 degrees: a wall seen at a slant recedes (a corridor's side) and is not a magnified block
const MIN_HOLD_BEATS := 1.0  # a stare shorter than a beat (0.35 to 0.43 s) is a turn passing a wall
const RAYS := 11  # across the stage strip, edge to edge (equal steps of screen width)
const VIEW_ASPECT := 1280.0 / 460.0  # the stage strip of a 1280 x 720 window, the narrowest picture we ship (tests/test_heralds_view.gd)
const MAX_M := 60.0
const TRANSIT_M := 0.9  # a moving camera this near a doorway it walks through is in transit (not judged)
const FLAGS := {"wh_saw_floor": true, "wh_vip_pass": true}  # every Warehouse entrance on offer (tests/test_heralds_view.gd)
const PATHS := ["gospel", "squadron", "ember"]
const SEED := 0
## Poses accepted with a reason (docs/art/CAMERA_CLEARANCE.md, "Exceptions", each with a shot): scene id -> {kinds: pose kinds (prefixes), why}. Listed, not counted as failures.
const EXCEPTIONS := {
	"hospital_late.quiet": {"kinds": ["window look"], "why": "the quiet room is 2.4 m wide and its default exit is behind the standpoint: the window's turn to the choices sweeps across a side wall for about a beat and a half"},
}
## The phase numbers a later scene is played at: the block's glance is glances[(phase * 4 + block + len(id)) % n] and its stroll strolls[floor(that / 3) % n] when that % 3 != 0
## (RunRail.ambient), so nine consecutive phases give every combination a scene can meet in a run (the run's own first scene is phase 1).
const PHASES := [2, 3, 4, 5, 6, 7, 8, 9, 10]

static var _walls: Dictionary = {}  # map id -> {sector id -> [wall]}
static var _maps: Dictionary = {}


# --- the rays --------------------------------------------------------------------------------------------------------------------------------

static func map_of(id: String) -> StoryMap:
	if not _maps.has(id):
		_maps[id] = StoryMap.load_chapter(id, false)
	return _maps[id]


static func walls_of(m: StoryMap) -> Dictionary:
	if not _walls.has(m.id):
		var by := {}
		for w in m.resolved_walls():
			var sid := str(w["sector"])
			if not by.has(sid):
				by[sid] = []
			by[sid].append(w)
		_walls[m.id] = by
	return _walls[m.id]


## Distance along the ray (origin, unit dir) to segment a-b, or INF.
static func _ray_seg(o: Vector2, d: Vector2, a: Vector2, b: Vector2) -> float:
	var e := b - a
	var den := d.cross(e)
	if absf(den) < 1.0e-9:
		return INF
	var ao := a - o
	var t := ao.cross(e) / den
	var u := ao.cross(d) / den
	if u < -1.0e-6 or u > 1.0 + 1.0e-6 or t < 0.0:
		return INF
	return t


static func _is_sky(sec: Dictionary) -> bool:
	return str(sec.get("ceil_tex", "")) == "sky" or "sky" in (sec.get("flags", []) as Array) or str(sec.get("sky", "")) != ""


## One ray from ground point `o` in sector `sec` at eye height `eye`, horizontal unit direction `d`, rising `slope` metres per metre. {s: horizontal metres to the
## first surface (MAX_M when none), what: a short description of it}.
static func cast(m: StoryMap, o: Vector2, sec: String, d: Vector2, eye: float, slope: float) -> Dictionary:
	var walls := walls_of(m)
	var s := 0.0
	var cur := sec
	for _hop in 64:
		var sd := m.sector(cur)
		if sd.is_empty():
			return {"s": s, "what": "outside the map", "face": 1.0}
		var best := INF
		var bw: Dictionary = {}
		for w in walls.get(cur, []):
			var t := _ray_seg(o, d, w["a"], w["b"])
			if t > s + 1.0e-4 and t < best:
				best = t
				bw = w
		var fl := float(sd["floor"])
		var ce := float(sd["ceiling"])
		if slope < -1.0e-6:
			var tf := (fl - eye) / slope
			if tf < best:
				return {"s": maxf(tf, s), "what": "floor of %s" % cur, "face": 1.0}
		if slope > 1.0e-6 and not _is_sky(sd):
			var tc := (ce - eye) / slope
			if tc < best:
				return {"s": maxf(tc, s), "what": "ceiling of %s" % cur, "face": 1.0}
		if bw.is_empty() or best > MAX_M:
			return {"s": MAX_M, "what": "open", "face": 0.0}
		var y := eye + slope * best
		var desc := "%s wall (%.1f, %.1f)-(%.1f, %.1f) %s" % [cur, bw["a"].x, bw["a"].y, bw["b"].x, bw["b"].y, bw["tex"]]
		var face := absf(d.dot(((bw["b"] as Vector2) - (bw["a"] as Vector2)).orthogonal().normalized()))  # 1 face-on, 0 edge-on
		if str(bw["portal"]) == "":
			return {"s": best, "what": desc, "face": face}
		var nb := m.sector(str(bw["portal"]))
		if nb.is_empty():
			return {"s": best, "what": desc, "face": face}
		if y <= float(nb["floor"]) + 0.02:
			return {"s": best, "what": "step up to %s: %s" % [bw["portal"], desc], "face": face}
		if y >= float(nb["ceiling"]) - 0.02 and not _is_sky(nb):
			return {"s": best, "what": "lintel over %s: %s" % [bw["portal"], desc], "face": face}
		s = best
		cur = str(bw["portal"])
	return {"s": s, "what": "too many portals", "face": 0.0}


## The sector the camera stands in (the pose's own, unless the point is not in it).
static func sector_of(m: StoryMap, pos: Vector2, sec: String) -> String:
	if sec != "" and m.inside(pos, sec, 0.0):
		return sec
	var s := m.sector_at(pos)
	return s if s != "" else sec


## What the camera sees at `pose`: {centre (m, camera depth), centre_what, share (of the picture's width nearer than FRAME_M), depths}.
## `full` false: when the centre ray already passes, the other rays are not cast (share 0): the pose cannot fail.
static func clearance(m: StoryMap, pose: Dictionary, full := true) -> Dictionary:
	var cam: Vector3 = pose["cam"]
	var yaw := float(pose["yaw"])
	var fwd0 := StoryProjector.forward(yaw)
	var c2 := Vector2(cam.x, cam.z)
	var sec := sector_of(m, c2, str(pose.get("sector", "")))
	var o := c2
	var lead := 0.0  # metres the rays start ahead of the eye
	var poly: PackedVector2Array = m.sector(sec).get("poly", PackedVector2Array())
	if sec == "" or poly.size() < 3 or StoryMap._dist_to_boundary(c2, poly) < StoryProjector.NEAR:
		# the eye is on a wall's line (a walk along a doorway line, a spine corridor's edge): that wall is seen edge-on and the picture starts at the near plane, so the
		# rays start there, in the sector that holds it; else 5 cm back, on the side the camera looks from
		var ahead := c2 + fwd0 * StoryProjector.NEAR
		var s_ahead := m.sector_at(ahead)
		if s_ahead != "":
			o = ahead
			sec = s_ahead
			lead = StoryProjector.NEAR
		else:
			o = c2 - fwd0 * 0.05
			sec = sector_of(m, o, sec)
	var p := deg_to_rad(float(pose.get("pitch", 0.0)))
	var fwd := StoryProjector.forward(yaw)
	var rgt := StoryProjector.right(yaw)
	var tan_h := tan(deg_to_rad(StoryProjector.FOV_V) * 0.5) * VIEW_ASPECT
	var depths: Array = []
	var near_w := 0.0
	var tot_w := 0.0
	var centre := MAX_M
	var centre_what := ""
	var centre_d := MAX_M
	var order: Array = range(RAYS)
	var mid := (RAYS - 1) / 2
	order.erase(mid)
	order.push_front(mid)  # (the centre first)
	for i in order:
		var f := -1.0 + 2.0 * float(i) / float(RAYS - 1)
		var h := fwd * cos(p) + rgt * (f * tan_h)
		var hl := h.length()
		var r := cast(m, o, sec, h / hl, cam.y, sin(p) / hl)
		var dep := (float(r["s"]) + lead * h.dot(fwd0) / hl) / hl
		depths.append(dep)
		var w := 0.5 if i == 0 or i == RAYS - 1 else 1.0
		tot_w += w
		var facing := float(r["face"]) >= FACE_COS
		if dep < FRAME_M and facing:
			near_w += w
		if i == mid:
			centre = dep if facing else MAX_M
			centre_d = dep
			if not full and centre >= CENTRE_M:
				return {"centre": centre, "centre_d": centre_d, "centre_what": str(r["what"]), "share": 0.0, "depths": [dep], "sector": sec}
			centre_what = str(r["what"])
	return {"centre": centre, "centre_d": centre_d, "centre_what": centre_what, "share": near_w / tot_w, "depths": depths, "sector": sec}


## The pose as a screenshot camera (RW_STORY_CAM=@x:z:yaw:pitch, src/story/story_stage.gd): shoot the failing frame with tools/story/shoot_heralds.sh-style runs.
static func cam_arg(pose: Dictionary) -> String:
	var c: Vector3 = pose["cam"]
	return "@%.2f:%.2f:%.1f:%.1f" % [c.x, c.z, float(pose["yaw"]), float(pose.get("pitch", 0.0))]


static func fails(c: Dictionary) -> bool:
	return float(c["centre"]) < CENTRE_M and float(c["share"]) > FRAME_SHARE


# --- the journey ------------------------------------------------------------------------------------------------------------------------------

## Every scene to check: [{data, id, entries: [{kind, from}]}] for the main run and the paths.
static func scenes(direct_all := false) -> Array:
	var out: Array = []
	var sets: Array = [RunData.load_files(RunData.RUN_PATH, RunData.MUSIC_PATH, RunData.PACKS_DIR, SEED)]  # (a fixed seed: the arrangement, so the chart's density and the moves' lengths, is the same every run)
	for pid in PATHS:
		sets.append(RunData.load_path(pid, SEED))
	for data in sets:
		var preds := {}
		for id in data.node_order:
			for nx in (data.nodes[id] as Dictionary).get("next", []):
				var to := str(nx["to"])
				if data.nodes.has(to):
					if not preds.has(to):
						preds[to] = []
					if id not in preds[to]:
						preds[to].append(id)
		for id in data.node_order:
			var n: Dictionary = data.nodes[id]
			var entries: Array = [{"kind": "direct", "from": ""}] if direct_all or (not data.is_path() and id == data.start_node()) else []
			var arrival: bool = id == data.start_node()  # a path's first scene is entered from the main run; the Warehouse from a path's ending
			for pr in preds.get(id, []):
				if str(data.nodes[pr]["world"]) != str(n["world"]):
					arrival = true
				elif pr != id:
					entries.append({"kind": "door", "from": pr})
			if arrival:
				entries.append({"kind": "arrival", "from": ""})
			out.append({"data": data, "id": id, "entries": entries})
	return out


## Plays scene `id` entered by `entry` with the perfect bot and the default exit. {player, t0, t_from, t_end, beat, laps, map, actions, entry}.
static func play(data: RunData, id: String, entry: Dictionary, phase := 2) -> Dictionary:
	var e := RunEngine.new(data)
	e.hotspots = RunHotspots.new(data, FLAGS.duplicate() if not data.is_path() else {}, {})
	var j := RunJourney.new(data)
	var kind := str(entry["kind"])
	var node: Dictionary = data.nodes[id]
	var map_id := str(node["map"])
	var m := map_of(map_id)
	j.face_fn = func(node_id: String, _place: String) -> Array:  # the run scene's window turn (RunPlay._window_face), with the map alone
		var pts: Array = []
		for h in e.hotspots.shown(3, true):
			if RunHotspots.window_of(h) != "final":
				continue
			var r := HotspotView.resolve(h["anchor"], map_of(str(data.nodes[node_id]["map"])), {})
			if bool(r["ok"]):
				var hp: Vector3 = r["pos"]
				pts.append([hp.x, hp.z, 1.0 if bool(h["default"]) else 0.0, hp.y])
		return pts
	var actions: Array = []
	var pre: Array = []
	if kind == "direct":  # (RunPlay starts a first scene whose home is not the map's start with a walk there over the countdown)
		e.begin(id)
		if str(node["waypoint"]) != m.start_id:
			pre.append({"t0": -4.0 * e.beat_s, "action": "player_move", "args": {"to": str(node["waypoint"]), "bars": 3.0, "style": "walk"}})
	else:
		e.arrive(id, 0.0, float(data.cfg["energy"]["start"]), phase - 1)  # a later phase of a run (the journey's arrival or door walk applies); the phase number picks the block's glance and stroll
		if kind == "door":
			j.run_world = str(node["world"])
			j.node_id = str(entry["from"])
			j.door_target = id
	var t0 := -1.0
	var t := 0.0
	var next_i := 0
	var held: Array = []
	var door := {}
	var beat := e.beat_s
	var t_end := INF
	while t < 4.0 * 64.0 * 4.0 * beat and not e.over:
		for ev in e.update(t):
			var k := str(ev["kind"])
			if k == "phase_start" and t0 < 0.0:
				t0 = float(ev["t"])
				beat = e.beat_s
				t_end = t0 + float(e.laps) * 64.0 * beat
			if k == "phase_start" and str(ev["node"]) != id:
				t = INF
				break
			if k in ["phase_start", "block_result", "lap_start"]:
				actions.append_array(j.on_event(ev, e))
		if t == INF or t > t_end:
			break
		while next_i < e.level.notes.size() and float(e.level.notes[next_i]["time"]) <= t:
			var n: Dictionary = e.level.notes[next_i]
			e.press(int(n["pad"]), float(n["time"]), int(n["pad"]))
			held.append({"pad": int(n["pad"]), "up": float(n["end_time"]) if n["type"] == "hold" else float(n["time"]) + 0.06})
			next_i += 1
		for hd in held.duplicate():
			if float(hd["up"]) <= t:
				e.release(int(hd["pad"]), float(hd["up"]), int(hd["pad"]))
				held.erase(hd)
		if e.window_open and not door.has(e.phase_n) and e.phase_beat_at(t) >= 61.0:
			door[e.phase_n] = true
			var to := e.selected_route()
			if data.nodes.has(to) and str(data.nodes[to]["world"]) == str(node["world"]) and to != id:
				actions.append_array(j.leave_walk(e.t_of(61.0), to, e))
		t += 1.0 / 30.0
	var p := StoryPlayer.new()
	p.setup(m, float(data.cfg["timing"]["bpm"]))
	var t_from := t0
	if kind == "door":  # the camera stands where the previous scene's rail ends (its top place) and walks through the door from three beats before the downbeat
		var prev: Dictionary = data.nodes[str(entry["from"])]
		var good: Array = prev["rail"]["good"]
		var top := str((good[good.size() - 1] as Dictionary)["to"]) if not good.is_empty() else str(prev["waypoint"])
		var rail: Dictionary = node["rail"]
		var wp := str(rail.get("arrive", ""))
		if wp == "":
			wp = str(node["waypoint"])
		pre.append({"t0": t0 - 12.0 * beat, "action": "player_move", "args": {"to": top, "style": "walk", "bars": 0.01, "cut": true}})
		pre.append({"t0": t0 - 3.0 * beat, "action": "player_move", "args": {"to": wp, "style": "walk", "bars": 4.0}})
		t_from = t0 - 3.0 * beat
	for a in pre:
		p.apply_action(a)
	for a in actions:
		if str(a.get("world", map_id)) == map_id:
			p.apply_action(a)
	return {"player": p, "t0": t0, "t_from": t_from, "t_end": t_end, "beat": beat, "laps": e.laps, "map": m, "actions": actions, "entry": entry, "errors": p.errors}


## What drives the camera at t (for the table): passage window, arrival walk, door walk, leave walk, herald look, window look, glance, stroll, move to <wp>, place <wp>.
static func kind_at(run: Dictionary, t: float) -> String:
	var p: StoryPlayer = run["player"]
	var t0 := float(run["t0"])
	var beat := float(run["beat"])
	var lb := fposmod((t - t0) / beat, 64.0)
	var ek := str(run["entry"]["kind"])
	if ek == "arrival" and t >= t0 and t < t0 + RunPassage.OPEN_BEATS * beat:
		return "passage window"
	if float(p.face_at(t)["w"]) > 0.05:
		return "window look" if lb >= 40.0 else "herald look"
	var mv: Dictionary = {}
	for ev in p.events():
		if float(ev["t0"]) <= t and ev["kind"] == "move":
			mv = ev
	var moving := not mv.is_empty() and t < float(mv["t1"])
	if absf(p.glance_at(t)) > 0.5 or absf(p.pitch_at(t)) > 0.5:
		return "glance"
	if moving:
		if bool(mv["walk"]):
			return "stroll"
		if t >= float(run["t_end"]) - 4.0 * beat:
			return "leave walk to %s" % mv["to"]
		if ek == "door" and t < t0 + 16.0 * beat:
			return "door walk to %s" % mv["to"]
		if ek == "arrival" and t < t0 + 16.0 * beat:
			return "arrival walk to %s" % mv["to"]
		return "move to %s" % mv["to"]
	if mv.is_empty():
		return "place %s" % ("start" if ek == "direct" else "?")
	return "place %s" % (mv["to"] if not bool(mv["walk"]) else "stroll end")


## True while the camera walks through a doorway: a journey move (not a stroll) under way whose route crosses a portal within TRANSIT_M of the eye (the jambs pass by
## in a beat) or that is in a sector it only passes through (a stair, a corridor between two rooms), or a move on a wall's line (a route along a row of doorways, the gospel maps' spine): that wall is edge-on to the eye, and the shots show the room beyond.
static func in_transit(m: StoryMap, pose: Dictionary, p: StoryPlayer, t: float) -> bool:
	if not bool(pose.get("moving", false)):
		return false
	var ev: Dictionary = p._event_at(t)
	if ev.is_empty() or str(ev.get("kind", "")) != "move" or ev.has("walk"):
		return false
	var o: Vector2 = pose["pos"]
	var sec := sector_of(m, o, str(pose.get("sector", "")))
	var poly: PackedVector2Array = m.sector(sec).get("poly", PackedVector2Array())
	if poly.size() >= 3 and StoryMap._dist_to_boundary(o, poly) < StoryProjector.NEAR:
		return true
	var legs: Array = ev.get("legs", [])
	if legs.size() > 2 and str(pose.get("sector", "")) != str(legs[0]) and str(pose.get("sector", "")) != str(legs[legs.size() - 1]):
		return true  # (a room or a stair the move only passes through)
	var pts: PackedVector2Array = ev.get("route", PackedVector2Array())
	for i in range(1, pts.size() - 1):  # (the inner points of a route are the midpoints of the portals it crosses)
		if pts[i].distance_to(o) < TRANSIT_M:
			return true
	return false


## The failing poses of one played entry, grouped into runs of consecutive samples of one kind: [{from_b, to_b, kind, centre, share, what, worst_t}]. Also counts samples.
## A stare held for less than MIN_HOLD_BEATS (consecutive failing samples, whatever drives the camera) is a head turning past a wall, not a pose: it is left out.
static func check_run(run: Dictionary, step_beats: float, dump: Array = []) -> Dictionary:
	var p: StoryPlayer = run["player"]
	var m: StoryMap = run["map"]
	var beat := float(run["beat"])
	var t0 := float(run["t0"])
	var t := float(run["t_from"])
	if str(run["entry"]["kind"]) == "arrival":
		t = t0  # (before the downbeat the passage frame is shut over the old world)
	var t_end := float(run["t_end"]) - 0.05
	var out: Array = []
	var streak: Array = []  # the runs of the current streak of failing samples
	var sf := {"from": 0.0}  # (a dictionary: the lambda below sees changes to it)
	var cur: Dictionary = {}
	var n := 0
	var flush := func(last_b: float) -> void:
		if not streak.is_empty() and last_b - float(sf["from"]) + step_beats >= MIN_HOLD_BEATS - 1.0e-3:
			out.append_array(streak)
		streak.clear()
	while t <= t_end:
		var pose := p.pose_at(t)
		var c := clearance(m, pose, not dump.is_empty())
		var tr := in_transit(m, pose, p, t)
		n += 1
		var b := (t - t0) / beat
		if not dump.is_empty():
			dump.append("%s,%s,%s,%.2f,%.2f,%.2f,%s,%s,%s" % [run["id"], run["entry"]["kind"], run["entry"]["from"], b, float(c["centre"]), float(c["share"]), kind_at(run, t), tr, str(c["centre_what"]).replace(",", ";")])
		if fails(c) and not tr:
			if streak.is_empty():
				sf["from"] = b
			var kd := kind_at(run, t)
			if not cur.is_empty() and str(cur["kind"]) == kd and b - float(cur["to_b"]) <= step_beats + 1.0e-3:
				cur["to_b"] = b
				if float(c["centre"]) < float(cur["centre"]):
					cur["centre"] = c["centre"]
					cur["share"] = c["share"]
					cur["what"] = c["centre_what"]
					cur["worst_t"] = t
					cur["cam"] = cam_arg(pose)
			else:
				cur = {"from_b": b, "to_b": b, "kind": kd, "centre": c["centre"], "share": c["share"], "what": c["centre_what"], "worst_t": t, "cam": cam_arg(pose)}
				streak.append(cur)
		else:
			flush.call(b - step_beats)
			cur = {}
		t += step_beats * beat
	flush.call((t - t0) / beat - step_beats)
	return {"fails": out, "samples": n}


## The whole check: [{scene, path, entry, from, fails: [...], samples}] over every scene and entry (only scene ids matching `only`, a regex, when given).
static func check_all(step_beats: float, only := "", dump: Array = [], direct_all := false) -> Array:
	var re: RegEx = null
	if only != "":
		re = RegEx.create_from_string(only)
	var out: Array = []
	for sc in scenes(direct_all):
		var data: RunData = sc["data"]
		var id := str(sc["id"])
		if re != null and re.search(id) == null:
			continue
		for entry in sc["entries"]:
			var row := {"scene": id, "path": data.path_id, "entry": entry["kind"], "from": entry["from"], "fails": [], "excepted": [], "samples": 0, "errors": []}
			var seen := {}
			for ph in ([1] if str(entry["kind"]) == "direct" else PHASES):
				var run := play(data, id, entry, ph)
				run["id"] = id
				var r := check_run(run, step_beats, dump)
				row["samples"] += int(r["samples"])
				for er in run["errors"]:
					if er not in row["errors"]:
						row["errors"].append(er)
				for f in r["fails"]:  # (the same pose in several phase numbers is one row, its phases listed)
					var key := "%s|%.1f|%.1f|%s" % [f["kind"], f["from_b"], f["to_b"], f["what"]]
					if seen.has(key):
						seen[key]["phases"].append(ph)
					else:
						f["phases"] = [ph]
						seen[key] = f
						row["excepted" if excepted(id, str(f["kind"])) else "fails"].append(f)
			out.append(row)
	return out


static func excepted(id: String, kind: String) -> bool:
	for k in (EXCEPTIONS.get(id, {}) as Dictionary).get("kinds", []):
		if kind.begins_with(str(k)):
			return true
	return false


static func world_of(row: Dictionary) -> String:
	var id := str(row["scene"])
	var w := id.get_slice(".", 0)
	return w if str(row["path"]) == "" else "%s/%s" % [row["path"], w]


static func table(rows: Array, key := "fails") -> String:
	var lines: Array = []
	lines.append("| scene | entry | phases | beats (from the scene's first downbeat) | pose | centre m | width near | nearest surface at the centre | camera (RW_STORY_CAM) |")
	lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
	for r in rows:
		var sid := str(r["scene"]) if str(r["path"]) == "" else "%s: %s" % [r["path"], r["scene"]]
		var ent := str(r["entry"]) + ("" if str(r["from"]) == "" else " from %s" % r["from"])
		for f in r.get(key, []):
			var phs: Array = f.get("phases", [])
			lines.append("| %s | %s | %s | %.1f to %.1f | %s | %.2f | %d%% | %s | %s |" % [sid, ent, "all" if phs.size() == PHASES.size() else ",".join(phs.map(func(x: int) -> String: return str(x))), float(f["from_b"]), float(f["to_b"]), f["kind"], float(f["centre"]), roundi(100.0 * float(f["share"])), f["what"], f.get("cam", "")])
	return "\n".join(lines)


static func summary(rows: Array) -> String:
	var by := {}
	var order: Array = []
	var total := 0
	var samples := 0
	for r in rows:
		var w := world_of(r)
		if not by.has(w):
			by[w] = {"poses": 0, "scenes": {}}
			order.append(w)
		by[w]["poses"] += (r["fails"] as Array).size()
		if not (r["fails"] as Array).is_empty():
			by[w]["scenes"][r["scene"]] = true
		total += (r["fails"] as Array).size()
		samples += int(r["samples"])
	var lines: Array = ["| world | failing poses | scenes with one |", "| --- | --- | --- |"]
	for w in order:
		lines.append("| %s | %d | %s |" % [w, by[w]["poses"], ", ".join((by[w]["scenes"] as Dictionary).keys()) if not (by[w]["scenes"] as Dictionary).is_empty() else "-"])
	lines.append("| **all** | **%d** | %d scene entries, %d samples |" % [total, rows.size(), samples])
	return "\n".join(lines)
