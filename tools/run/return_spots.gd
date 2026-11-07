extends SceneTree
## Where a path's return object may stand (work package N2.5): checks the default spot of tools/run/returns_common.py in every scene of the three paths against the real rail
## camera, and searches a better one where the default fails. A survey for whoever sets the per-scene overrides; the game does not read it.
##
##     bash tools/dev/godot.sh --headless --audio-driver Dummy --path . -s tools/run/return_spots.gd -- [--only <regex>] [--ahead 4.2] [--left 2.6] [--out file.json] [--check file.json]
##
## For each scene it plays the scene as a player enters it (the run's own journey, the perfect bot: tools/art/camera_clearance_check.gd), samples the camera every two beats over
## the opening bars (beats 0 to 16, two phase numbers, so two glances and strolls) and asks of a spot: inside the map and clear of walls' edges; in sight at every sample (inside
## the narrowest picture we ship, no wall between the eye and the door's foot and middle); at least CLEAR_HOTSPOT_M from every other hotspot's anchor (0.75 m is the rule, a spare is
## kept), CLEAR_THING_M from a thing, home or occluder of the map and from a doorway; and not across the picture from another choice. `--check` reads {scene: [x, y, z]} (the
## table the generators write) and judges those spots instead of the default.

const OPEN_BEATS := [12.0, 14.0, 16.0, 40.0, 44.0, 48.0, 52.0, 56.0]  # the camera is at its place from beat 8 to 12 (an entry walks in first); the window look turns to the choices from beat 40; the walk between is not judged
const MUST_SEE := 3  # the first three samples (the settled camera) must all see the door; of the rest, SEE_SHARE of them
const PHASES := [2, 3]
var SEE_SHARE := 0.6
const WINDOW_FROM := 3
var F_MAX := -0.30  # the door's centre at the settled camera at most this far from the picture's middle to the left (-1 the left edge): not over the onward exits
var EARLY_MISS := 0  # settled samples (beats 12 to 16) that may miss
var WINDOW_MISS := 2  # window samples that may miss (of 10, two phases)  # the samples from this index are the choice window (beats 40 to 56): at most one may miss
const PATHS := ["gospel", "squadron", "ember"]
const ASPECT := 1280.0 / 460.0  # the stage strip of a 1280 x 720 window, the narrowest picture we ship
const SIDE_MAX := 0.88  # the door's centre inside this share of the half-picture at every sample
const DEPTH_MIN := 2.0
var DEPTH_MAX := 11.5
var CLEAR_HOTSPOT_M := 1.1
var CLEAR_THING_M := 0.9
const CLEAR_PORTAL_M := 1.2
const WALL_MIN_M := 0.25  # centre of the door's foot at least this far from a sector's edge
var SEP_F := 0.34  # screen separation (share of the half-picture) from another choice's anchor at the opening pose
const DOOR_H := 3.0
const DOOR_CENTRE_Y := 1.5


func _init() -> void:
	_run()


func _run() -> void:
	await process_frame
	var CC: GDScript = load("res://tools/art/camera_clearance_check.gd")
	var args := OS.get_cmdline_user_args()
	var only := ""
	var ahead := 4.2
	var left := 2.6
	var out_path := ""
	var check_path := ""
	var i := 0
	while i < args.size():
		match args[i]:
			"--only":
				only = args[i + 1]
				i += 1
			"--ahead":
				ahead = float(args[i + 1])
				i += 1
			"--left":
				left = float(args[i + 1])
				i += 1
			"--out":
				out_path = args[i + 1]
				i += 1
			"--check":
				check_path = args[i + 1]
				i += 1
			"--trace":  # the camera of one scene (path/scene id) at every second beat, for every way in
				_trace(CC, args[i + 1])
				quit(0)
				return
		i += 1
	var table: Dictionary = {}
	if check_path != "":
		table = JSON.parse_string(FileAccess.get_file_as_string(check_path))
	var rx: RegEx = null
	if only != "":
		rx = RegEx.create_from_string(only)
	var report := {}
	var bad := 0
	for pid in PATHS:
		var data := RunData.load_path(pid, 0)
		for id in data.node_order:
			var gid := "%s/%s" % [pid, id]
			if rx != null and rx.search(gid) == null:
				continue
			var node: Dictionary = data.nodes[id]
			var m: StoryMap = CC.map_of(str(node["map"]))
			var poses_by_phase: Array = []
			for ph in PHASES:
				var run: Dictionary = CC.play(data, id, {"kind": "direct", "from": ""}, ph)
				var p: StoryPlayer = run["player"]
				var poses: Array = []
				for b in OPEN_BEATS:
					poses.append(p.pose_at(float(run["t0"]) + b * float(run["beat"])))
				poses_by_phase.append(poses)
			var poses_all: Array = []
			for ps in poses_by_phase:
				poses_all.append_array(ps)
			var home: Dictionary = poses_by_phase[0][1]  # beat 14: the camera settled on its place
			var cam2 := Vector2((home["cam"] as Vector3).x, (home["cam"] as Vector3).z)
			var yaw := float(home["yaw"])
			var fwd := StoryProjector.forward(yaw)
			var rgt := StoryProjector.right(yaw)
			var good: Array = node["rail"]["good"]  # the camera ends its walk at the rail's top place and looks at the choices from there: the default spot is measured from it
			var wpn := m.waypoint(str((good[good.size() - 1] as Dictionary)["to"]) if not good.is_empty() else str(node["waypoint"]))
			var default_xz: Vector2 = (wpn["at"] as Vector2) + StoryProjector.forward(float(wpn["yaw"])) * ahead - StoryProjector.right(float(wpn["yaw"])) * left
			var others := _others(data, id, m)
			var res: Dictionary
			var chosen := default_xz
			if check_path != "":
				var v: Array = table.get(gid, [])
				if v.is_empty():
					report[gid] = {"ok": false, "why": ["no spot in the table"]}
					bad += 1
					continue
				chosen = Vector2(float(v[0]), float(v[2]))
			res = _judge(CC, m, chosen, poses_all, home, others)
			var entry := {"ok": res["ok"], "why": res["why"], "xz": [snappedf(chosen.x, 0.01), snappedf(chosen.y, 0.01)], "f": res["f"], "depth": res["depth"]}
			if not bool(res["ok"]) and check_path == "":
				var best := _search(CC, m, cam2, fwd, rgt, poses_all, home, others)
				entry["best"] = best
				if best.is_empty():
					bad += 1
			elif not bool(res["ok"]):
				bad += 1
			report[gid] = entry
			print("%s %s xz=(%.2f, %.2f) f=%.2f depth=%.1f %s%s" % ["ok  " if bool(res["ok"]) else "FAIL", gid, chosen.x, chosen.y, float(res["f"]), float(res["depth"]), ", ".join(PackedStringArray(res["why"])),
				"" if not entry.has("best") else ("  best=" + (str(entry["best"]["xz"]) + " f=" + str(entry["best"]["f"]) if not (entry["best"] as Dictionary).is_empty() else "none"))])
	if out_path != "":
		var fh := FileAccess.open(out_path, FileAccess.WRITE)
		fh.store_string(JSON.stringify(report, " "))
		fh.close()
	print("scenes judged: %d, not ok: %d" % [report.size(), bad])
	quit(1 if bad > 0 else 0)


## Positions (x, z) of everything the door must stand clear of: [{at: Vector2, m: metres, what}]. Other choices' anchors first (the return's own row is not there yet).
func _others(data: RunData, id: String, m: StoryMap) -> Array:
	var out: Array = []
	for h in data.hotspots_of(id):
		if str(h["id"]).ends_with(".return"):
			continue
		var an: Dictionary = h["anchor"]
		var at := Vector2.INF
		if an.has("actor"):
			var hm: Dictionary = m.home(str(an["actor"]))
			if not hm.is_empty():
				at = hm["at"]
		else:
			var r := HotspotView.resolve(an, m, {})
			if bool(r.get("ok", false)):
				at = Vector2((r["pos"] as Vector3).x, (r["pos"] as Vector3).z)
		if at != Vector2.INF:
			out.append({"at": at, "m": CLEAR_HOTSPOT_M, "what": "choice " + str(h["id"]), "choice": true})
	for t in m.things:
		if str(t.get("kind", "")) == "light":
			continue
		out.append({"at": t["at"], "m": CLEAR_THING_M, "what": "thing " + str(t["id"]), "choice": false})
	for k in m.homes:
		out.append({"at": (m.homes[k] as Dictionary)["at"], "m": CLEAR_THING_M, "what": "home " + str(k), "choice": false})
	for o in m.occluders:
		out.append({"at": o["at"], "m": CLEAR_THING_M, "what": "occluder " + str(o["id"]), "choice": false})
	for pt in m.portals():
		out.append({"at": pt["mid"], "m": CLEAR_PORTAL_M, "what": "doorway", "choice": false})
	return out


func _judge(CC: GDScript, m: StoryMap, xz: Vector2, poses: Array, home: Dictionary, others: Array) -> Dictionary:
	var why: Array = []
	var sec := m.sector_at(xz)
	if sec == "":
		return {"ok": false, "why": ["outside the map"], "f": 0.0, "depth": 0.0}
	var poly: PackedVector2Array = m.sector(sec).get("poly", PackedVector2Array())
	if StoryMap._dist_to_boundary(xz, poly) < WALL_MIN_M:
		why.append("on a wall's edge")
	var tan_h := tan(deg_to_rad(StoryProjector.FOV_V) * 0.5) * ASPECT
	var hidden := 0
	var hidden_early := 0
	var hidden_window := 0
	var sep_hits := 0
	var seen_f := 0.0
	var f_home := 0.0
	var d_home := 0.0
	for pose in poses:
		var cam: Vector3 = pose["cam"]
		var yaw := float(pose["yaw"])
		var rel := xz - Vector2(cam.x, cam.z)
		var dep := rel.dot(StoryProjector.forward(yaw))
		var lat := rel.dot(StoryProjector.right(yaw))
		var f := lat / (maxf(dep, 0.01) * tan_h)
		if pose == home:
			f_home = f
			d_home = dep
		var k_idx := poses.find(pose)
		var early: bool = (k_idx % OPEN_BEATS.size()) < MUST_SEE
		if dep < DEPTH_MIN or dep > DEPTH_MAX or absf(f) > SIDE_MAX:
			hidden += 1
			hidden_early += 1 if early else 0
			hidden_window += 1 if (k_idx % OPEN_BEATS.size()) >= WINDOW_FROM else 0
			continue
		seen_f += f
		for o in others:
			if not bool(o["choice"]):
				continue
			var rel3: Vector2 = (o["at"] as Vector2) - Vector2(cam.x, cam.z)
			var dep3 := rel3.dot(StoryProjector.forward(yaw))
			if dep3 > 0.5 and absf(rel3.dot(StoryProjector.right(yaw)) / (dep3 * tan_h) - f) < SEP_F:
				sep_hits += 1
				break
		var dist := rel.length()
		var dir := rel / maxf(dist, 0.001)
		var csec: String = CC.sector_of(m, Vector2(cam.x, cam.z), str(pose.get("sector", "")))
		var blocked := false
		for y in [0.1, DOOR_CENTRE_Y, 2.8]:
			var r: Dictionary = CC.cast(m, Vector2(cam.x, cam.z), csec, dir, cam.y, (y - cam.y) / dist)
			if float(r["s"]) < dist - 0.35:
				blocked = true
		if blocked:
			hidden += 1
			hidden_early += 1 if early else 0
			hidden_window += 1 if (k_idx % OPEN_BEATS.size()) >= WINDOW_FROM else 0
	if hidden_early > EARLY_MISS or hidden_window > WINDOW_MISS or float(hidden) > float(poses.size()) * (1.0 - SEE_SHARE):
		why.append("out of sight at %d of %d samples (%d of the settled ones)" % [hidden, poses.size(), hidden_early])
	if sep_hits > WINDOW_MISS:
		why.append("on screen over or beside another choice at %d of %d samples" % [sep_hits, poses.size()])
	if f_home > F_MAX:
		why.append("at the middle or right of the opening picture (f %.2f)" % f_home)
	for o in others:
		var d: float = xz.distance_to(o["at"])
		if d < float(o["m"]):
			why.append("%.2f m from %s" % [d, o["what"]])
	return {"ok": why.is_empty(), "why": why, "f": snappedf(f_home, 0.01), "depth": snappedf(d_home, 0.1)}


## The best clear spot in the opening camera's frame: left of the picture's middle, 3.5 to 6 m ahead, near a wall. {} when none.
func _search(CC: GDScript, m: StoryMap, cam2: Vector2, fwd: Vector2, rgt: Vector2, poses: Array, home: Dictionary, others: Array) -> Dictionary:
	var base := [SEE_SHARE, CLEAR_HOTSPOT_M, CLEAR_THING_M, SEP_F, WINDOW_MISS, EARLY_MISS, DEPTH_MAX, F_MAX]
	var tiers := [base, [0.5, 1.0, 0.8, 0.28, 4, 0, 11.5, -0.25], [0.4, 0.9, 0.7, 0.22, 6, 0, 11.5, -0.2], [0.3, 0.9, 0.7, 0.16, 8, 2, 22.0, 0.5]]
	for ti in tiers.size():
		SEE_SHARE = tiers[ti][0]
		CLEAR_HOTSPOT_M = tiers[ti][1]
		CLEAR_THING_M = tiers[ti][2]
		SEP_F = tiers[ti][3]
		WINDOW_MISS = tiers[ti][4]
		EARLY_MISS = tiers[ti][5]
		DEPTH_MAX = tiers[ti][6]
		F_MAX = tiers[ti][7]
		# (the "others" list carries the margins it was built with: rebuild them for the tier)
		var o2: Array = []
		for o in others:
			var mm: float = CLEAR_HOTSPOT_M if bool(o["choice"]) else (CLEAR_PORTAL_M if str(o["what"]) == "doorway" else CLEAR_THING_M)
			o2.append({"at": o["at"], "m": mm, "what": o["what"], "choice": o["choice"]})
		var r := _search_tier(CC, m, cam2, fwd, rgt, poses, home, o2)
		if not r.is_empty():
			r["tier"] = ti
			SEE_SHARE = base[0]
			CLEAR_HOTSPOT_M = base[1]
			CLEAR_THING_M = base[2]
			SEP_F = base[3]
			WINDOW_MISS = base[4]
			EARLY_MISS = base[5]
			DEPTH_MAX = base[6]
			F_MAX = base[7]
			return r
	SEE_SHARE = base[0]
	CLEAR_HOTSPOT_M = base[1]
	CLEAR_THING_M = base[2]
	SEP_F = base[3]
	WINDOW_MISS = base[4]
	EARLY_MISS = base[5]
	DEPTH_MAX = base[6]
	F_MAX = base[7]
	return {}


func _search_tier(CC: GDScript, m: StoryMap, cam2: Vector2, fwd: Vector2, rgt: Vector2, poses: Array, home: Dictionary, others: Array) -> Dictionary:
	var tan_h := tan(deg_to_rad(StoryProjector.FOV_V) * 0.5) * ASPECT
	var best := {}
	var best_s := -INF
	var d := 2.5
	while d <= 22.0:
		var l := -7.0
		while l <= 7.0:
			var xz := cam2 + fwd * d + rgt * l
			var res := _judge(CC, m, xz, poses, home, others)
			if bool(res["ok"]):
				var sec := m.sector_at(xz)
				var wd := StoryMap._dist_to_boundary(xz, m.sector(sec).get("poly", PackedVector2Array()))
				var s := -absf(float(res["f"]) + 0.65) * 3.0 - absf(float(res["depth"]) - 4.5) * 0.4 - minf(wd, 3.0) * 0.5
				if s > best_s:
					best_s = s
					best = {"xz": [snappedf(xz.x, 0.01), snappedf(xz.y, 0.01)], "f": res["f"], "depth": res["depth"], "wall_m": snappedf(wd, 0.1)}
			l += 0.25
		d += 0.5
	return best


func _trace(CC: GDScript, gid: String) -> void:
	var parts := gid.split("/")
	for sc in CC.scenes(true):
		var data: RunData = sc["data"]
		if data.path_id != parts[0] or str(sc["id"]) != parts[1]:
			continue
		var node: Dictionary = data.nodes[sc["id"]]
		var m: StoryMap = CC.map_of(str(node["map"]))
		print("scene %s home %s %s" % [gid, node["waypoint"], str(m.waypoint(str(node["waypoint"])))])
		for g in (node["rail"]["good"] as Array):
			print("  good %s %s" % [g["to"], str(m.waypoint(str(g["to"])))])
		for en in sc["entries"]:
			var run: Dictionary = CC.play(data, sc["id"], en, 2)
			var p: StoryPlayer = run["player"]
			print("  entry %s from %s" % [en["kind"], en["from"]])
			for b in range(0, 33, 2):
				var pose := p.pose_at(float(run["t0"]) + float(b) * float(run["beat"]))
				var c: Vector3 = pose["cam"]
				print("    beat %2d cam (%.2f, %.2f) yaw %.1f" % [b, c.x, c.z, float(pose["yaw"])])
