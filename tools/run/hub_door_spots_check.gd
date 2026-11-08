## (no class_name: tools/run/hub_door_spots.gd loads it by path, after the autoloads are in)
extends RefCounted
## The judging and the search of tools/run/hub_door_spots.gd (see there).

const ASPECT := 1280.0 / 460.0
const SIDE_MAX := 0.7  # the door's middle inside this share of the half-picture
const DEPTH_MIN := 5.0  # (nearer, a 2.4 m door's foot is under the picture)
const DEPTH_MAX := 11.0
const WALL_MIN_M := 0.45
## Tiers of the search, strict first: [clear of another choice (m), screen separation from another choice (share of the half-picture), window samples that may miss]
const TIERS := [[1.4, 0.16, 1], [1.1, 0.1, 2], [0.9, 0.06, 4]]
static var clear_m := 1.4
static var sep_f := 0.16
static var miss_max := 1


## The other choices' anchors of the scene (the door's own row left out) and the heralds' feet: [Vector2].
static func others_of(data: RunData, id: String, door: String, m: StoryMap) -> Array:
	var out: Array = []
	for h in data.hotspots_of(id):
		if str(h["id"]) == door:
			continue
		var an: Dictionary = h["anchor"]
		if an.has("actor"):
			var hm: Dictionary = m.home(str(an["actor"]))
			if not hm.is_empty():
				out.append(hm["at"])
		else:
			var r := HotspotView.resolve(an, m, {})
			if bool(r.get("ok", false)):
				out.append(Vector2((r["pos"] as Vector3).x, (r["pos"] as Vector3).z))
		if (h as Dictionary).has("herald"):
			var hp := StoryHeralds.look_points(h["herald"], m, 0.0)
			if hp.size() >= 3:
				out.append(Vector2(float(hp[2][0]), float(hp[2][1])))
	return out


static func judge(m: StoryMap, xz: Vector2, poses: Array, others: Array) -> Dictionary:
	var why: Array = []
	var sec := m.sector_at(xz)
	if sec == "":
		return {"ok": false, "why": ["outside the map"], "seen": 0}
	if StoryMap._dist_to_boundary(xz, m.sector(sec).get("poly", PackedVector2Array())) < WALL_MIN_M:
		why.append("on a wall's edge")
	for o in others:
		if xz.distance_to(o) < clear_m:
			why.append("%.2f m from a choice" % xz.distance_to(o))
			break
	var tan_h := tan(deg_to_rad(StoryProjector.FOV_V) * 0.5) * ASPECT
	var miss := 0
	var close := 0
	for pose in poses:
		var cam: Vector3 = pose["cam"]
		var c2 := Vector2(cam.x, cam.z)
		var fwd := StoryProjector.forward(float(pose["yaw"]))
		var rgt := StoryProjector.right(float(pose["yaw"]))
		var rel := xz - c2
		var dep := rel.dot(fwd)
		var f := rel.dot(rgt) / (maxf(dep, 0.01) * tan_h)
		if dep < DEPTH_MIN or dep > DEPTH_MAX or absf(f) > SIDE_MAX:
			miss += 1
			continue
		var d := rel.length()
		var s := m.sight(c2, str(pose.get("sector", "")), rel / d, cam.y)
		if float(s["m"]) < d - 0.4:
			miss += 1
			continue
		for o in others:
			var r2: Vector2 = (o as Vector2) - c2
			var d2 := r2.dot(fwd)
			if d2 > 0.5 and absf(r2.dot(rgt) / (d2 * tan_h) - f) < sep_f:
				close += 1
				break
	if miss > miss_max:
		why.append("out of the window's picture at %d of %d samples" % [miss, poses.size()])
	if close > miss_max:
		why.append("on screen over another choice at %d of %d samples" % [close, poses.size()])
	return {"ok": why.is_empty(), "why": why, "seen": poses.size() - miss}


## The best spot of sector `sec`'s room seen from the window: every 0.25 m inside the room's sectors, judged; of those that pass, the one nearest the picture's side (|f| about 0.55)
## and 5 m deep. {} when none.
static func search(m: StoryMap, poses: Array, others: Array, sec: String) -> Dictionary:
	for t in TIERS:
		clear_m = t[0]
		sep_f = t[1]
		miss_max = t[2]
		var r := _search(m, poses, others, sec)
		if not r.is_empty():
			r["tier"] = TIERS.find(t)
			clear_m = TIERS[0][0]
			sep_f = TIERS[0][1]
			miss_max = TIERS[0][2]
			return r
	clear_m = TIERS[0][0]
	sep_f = TIERS[0][1]
	miss_max = TIERS[0][2]
	return {}


static func _search(m: StoryMap, poses: Array, others: Array, sec: String) -> Dictionary:
	var room := m.room_of(sec)
	var best := {}
	var best_s := -INF
	var p0: Dictionary = poses[2]
	var cam: Vector3 = p0["cam"]
	var c2 := Vector2(cam.x, cam.z)
	var fwd := StoryProjector.forward(float(p0["yaw"]))
	var rgt := StoryProjector.right(float(p0["yaw"]))
	var tan_h := tan(deg_to_rad(StoryProjector.FOV_V) * 0.5) * ASPECT
	var d := DEPTH_MIN
	while d <= DEPTH_MAX:
		var l := -8.0
		while l <= 8.0:
			var xz := c2 + fwd * d + rgt * l
			var s_id := m.sector_at(xz)
			if s_id != "" and m.room_of(s_id) == room and m.sector(s_id).get("floor", 0.0) == m.sector(sec).get("floor", 0.0):
				var res := judge(m, xz, poses, others)
				if bool(res["ok"]):
					var f := l / (d * tan_h)
					var sc := -absf(absf(f) - 0.55) * 3.0 - absf(d - 5.0) * 0.4
					if sc > best_s:
						best_s = sc
						best = {"xz": [snappedf(xz.x, 0.05), snappedf(xz.y, 0.05)], "seen": res["seen"], "f": snappedf(f, 0.01), "sector": s_id}
			l += 0.25
		d += 0.25
	return best
