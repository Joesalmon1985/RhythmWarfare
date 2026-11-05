class_name StoryMap
extends RefCounted
## A chapter's 2.5D map (content/story/maps/<chapter>.json, docs/STORY_25D_PLAN.md section 3): sectors (convex floor/ceiling polygons
## with a height range), walls (portals join two sectors), billboard things, an actor home and a waypoint list for the player's rail.
## Pure logic, no nodes, no renderer. Coordinates are (x, z) metres on the ground plane (z grows toward the audience's back wall); a yaw of
## 0 degrees looks toward -z, and a positive yaw turns left (forward = (-sin yaw, -cos yaw)), the way Godot's Camera3D rotation.y does.
##
## Validation (errors[]): every sector polygon is simple, convex, non-degenerate and does not overlap another; ceilings clear floors;
## every wall lies on one edge of its sector, every portal also on one edge of the sector on the other side (which sees it implicitly
## from its side, so a portal is declared once); texture names exist (and their files when art is checked); every waypoint, home and thing
## lies inside its sector (waypoints and homes keep a margin from the walls); every sector is reachable from the start waypoint through
## portals; chapter checks: every actor has a home, every player_move / player_look target is a waypoint or actor.

const PATH := "res://content/story/maps/%s.json"
const EPS := 1.0e-3
const HOME_MARGIN := 0.25
const WAYPOINT_MARGIN := 0.3
const ANIMS := ["none", "pulse", "flicker", "rotate", "bob", "sway", "pump"]
const ANIM_MODES := ["scroll", "pulse", "flicker", "swap"]
const MOVE_STYLES := ["walk", "stagger", "run", "climb", "carried"]
const BANDS := ["quiet", "dancing", "hype", "euphoric"]  # the energy bands of the chapter files (StoryData.band_of)
const DANCE_FLAGS := ["dance_floor", "stage"]  # the only sectors where "dance" may appear in an activity list
const ROLES := ["dancer", "on_stage", "dj", "queasy", "sick", "recovered", "out"]

var id := ""
var art := ""  # assets/story/<art>/ holds the textures
var raw: Dictionary = {}
var units_per_m := 1.0
var eye_height := 1.6
var start_id := ""
var textures: Dictionary = {}  # name -> file relative to the art folder
var sectors: Array = []  # {id, poly: PackedVector2Array (counter-clockwise), floor, ceiling, floor_tex, ceil_tex, wall_tex, light, tint: Color, room, flags}
var things: Array = []
var lights: Array = []  # static light sources (things of kind "light"): {id, sector, at: Vector2, y (above the sector floor), radius (m), color: Color, strength, cone?: {yaw, angle}, sectors?: Array}; StoryWorld bakes them into vertex colours
var homes: Dictionary = {}  # actor id -> {sector, at: Vector2}
var waypoints: Dictionary = {}  # id -> {at: Vector2, yaw: float (degrees), sector}
var occluders: Array = []  # {id, sprite (a texture name of `textures`), sector, at: Vector2, width, height (m)} drawn over the crowd when nearer than a dancer
var spots: Dictionary = {}  # named places the crowd directives use: {sector, at: Vector2, ...} (door with `slots`, circle with `radii` and `open`, riser, side_l, side_r)
var silhouettes: Dictionary = {}  # rear-row silhouette id -> {sector, at: Vector2}
var sky: Dictionary = {}
var rooms: Dictionary = {}  # room id -> {palette: the chapter palette the room's light switches to when the player walks in}
var palette_weight := 0.25  # how much the stage palette (one colour per bar) overrides the tint of a dance floor or stage sector: 1 in Night One (the club), a little elsewhere so a ward stays blue and a lab stays green
var fog: Dictionary = {}  # optional {color: hex, density}: the chapter's haze (a hospital is light, the pit is red)
var animated: Array = []  # animated surfaces: {tex, mode: scroll|pulse|flicker|glow, speed?, rate?, amount?, bright?}
var errors: Array = []

var _sector_index: Dictionary = {}
var _walls_in: Array = []  # explicit walls as authored
var _walls_out: Array = []  # resolved (explicit, implicit reverse portals, filled gaps)
var _portals: Array = []  # {a, b, p0, p1, mid}


static func load_chapter(chapter: String, check_files := true) -> StoryMap:
	var path := PATH % chapter
	var m := StoryMap.new()
	m.id = chapter
	m.art = chapter
	if not FileAccess.file_exists(path):
		m.errors.append("map file missing: " + path)
		return m
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if typeof(parsed) != TYPE_DICTIONARY:
		m.errors.append("%s is not a JSON object" % path)
		return m
	m.art = str(parsed.get("art", chapter))  # a map may borrow another art folder (the Bassment's zones share assets/story/bassment/)
	m.build(parsed, check_files)
	return m


static func from_dict(d: Dictionary, chapter := "test", check_files := false) -> StoryMap:
	var m := StoryMap.new()
	m.id = chapter
	m.art = chapter
	m.build(d, check_files)
	return m


func build(d: Dictionary, check_files: bool) -> void:
	raw = d
	units_per_m = float(d.get("units_per_m", 1.0))
	eye_height = float(d.get("eye_height", 1.6))
	if units_per_m <= 0.0:
		errors.append("units_per_m must be positive")
	if eye_height <= 0.0:
		errors.append("eye_height must be positive")
	textures = d.get("textures", {})
	for k in textures:
		if check_files and str(textures[k]).begins_with("res://"):  # a `res://` texture lives outside the chapter (the blackjack table)
			if not ResourceLoader.exists(str(textures[k])):
				errors.append("texture %s: file %s is missing" % [k, textures[k]])
		elif check_files and not FileAccess.file_exists("res://assets/story/%s/%s" % [art, str(textures[k])]) and not ResourceLoader.exists("res://assets/story/%s/%s" % [art, str(textures[k])]):
			errors.append("texture %s: file %s is missing" % [k, textures[k]])
	sky = d.get("sky", {}) if typeof(d.get("sky", {})) == TYPE_DICTIONARY else {}
	rooms = d.get("rooms", {}) if typeof(d.get("rooms", {})) == TYPE_DICTIONARY else {}
	palette_weight = clampf(float(d.get("palette_weight", 0.25)), 0.0, 1.0)
	fog = d.get("fog", {}) if typeof(d.get("fog", {})) == TYPE_DICTIONARY else {}
	animated = d.get("animated", []) if typeof(d.get("animated", [])) == TYPE_ARRAY else []
	for an in animated:
		if typeof(an) != TYPE_DICTIONARY or not textures.has(str(an.get("tex", ""))) or str(an.get("mode", "")) not in ANIM_MODES:
			errors.append("animated surface %s: needs a map texture and a mode of %s" % [an, ANIM_MODES])
	_build_sectors(d.get("sectors", []))
	_build_walls(d.get("walls", []))
	_build_things(d.get("things", []))
	_build_waypoints(d.get("waypoints", []))
	start_id = str(d.get("start", ""))
	if start_id == "" and not waypoints.is_empty():
		start_id = str(waypoints.keys()[0])
	if not waypoints.has(start_id):
		errors.append("start waypoint %s is not a waypoint" % start_id)
	_build_homes(d.get("homes", []))
	_build_spots(d.get("spots", {}))
	_build_silhouettes(d.get("silhouettes", []))
	_build_occluders(d.get("occluders", []))
	_check_reachability()
	if errors.is_empty():
		_resolve_walls()


# --- construction and per-element checks ---------------------------------------------------------------------------------------------

func _pt(a: Variant, where: String) -> Vector2:
	if typeof(a) != TYPE_ARRAY or (a as Array).size() != 2:
		errors.append("%s: a point is [x, z]" % where)
		return Vector2.ZERO
	return Vector2(float(a[0]), float(a[1]))


func _tex_ok(name: String, where: String) -> void:
	if name != "" and name != "sky" and not textures.has(name):
		errors.append("%s: unknown texture %s" % [where, name])


func _build_sectors(list: Array) -> void:
	for s in list:
		var sid := str(s.get("id", ""))
		if sid == "" or _sector_index.has(sid):
			errors.append("sector id %s missing or duplicated" % sid)
			continue
		var pts := PackedVector2Array()
		for p in s.get("polygon", []):
			pts.append(_pt(p, "sector " + sid))
		var sec := {"id": sid, "floor": float(s.get("floor", 0.0)), "ceiling": float(s.get("ceiling", 3.0)),
			"floor_tex": str(s.get("floor_tex", "")), "ceil_tex": str(s.get("ceil_tex", "")), "wall_tex": str(s.get("wall_tex", "")),
			"light": float(s.get("light", 0.6)), "ambient": float(s.get("ambient", -1.0)), "tint": Color.html(str(s.get("tint", "#ffffff"))), "room": str(s.get("room", "main")),
			"flags": s.get("flags", [])}
		sec["activities"] = _build_activities(sid, s.get("activities", {}), sec["flags"])
		if pts.size() < 3:
			errors.append("sector %s: a polygon needs 3 points or more" % sid)
		else:
			if _signed_area(pts) < 0.0:
				pts.reverse()
			sec["poly"] = pts
			_check_polygon(sid, pts)
		if float(sec["ceiling"]) <= float(sec["floor"]) + EPS:
			errors.append("sector %s: ceiling must be above the floor" % sid)
		if float(sec["light"]) < 0.0 or float(sec["light"]) > 1.0:
			errors.append("sector %s: light is 0..1" % sid)
		for k in ["floor_tex", "ceil_tex", "wall_tex"]:
			_tex_ok(str(sec[k]), "sector " + sid)
		if not sec.has("poly"):
			sec["poly"] = PackedVector2Array()
		_sector_index[sid] = sectors.size()
		sectors.append(sec)
	for i in sectors.size():
		for j in range(i + 1, sectors.size()):
			_check_overlap(sectors[i], sectors[j])


## The sector's activities by mood band (docs/STORY_25D_ART_DIRECTION.md 2.C): {band: [activity names]}. The bands quiet, dancing and hype are required (euphoric falls back to
## hype); every name is a StoryCharacter activity; "dance" only appears on dance_floor or stage sectors and never in the quiet band. A sector without the key gets defaults by flag,
## which `activities_authored` reports (the tests require every sector to author its own).
func _build_activities(sid: String, raw_acts: Variant, flags: Array) -> Dictionary:
	var out := {}
	if typeof(raw_acts) != TYPE_DICTIONARY or (raw_acts as Dictionary).is_empty():
		return default_activities(flags)
	for band in raw_acts:
		if band not in BANDS:
			errors.append("sector %s: activities has unknown band %s" % [sid, band])
			continue
		var names: Array = []
		for n in raw_acts[band]:
			if str(n) not in StoryCharacter.ACTIVITIES:
				errors.append("sector %s: unknown activity %s" % [sid, n])
			elif str(n) == "dance" and (str(band) == "quiet" or not _any_in(flags, DANCE_FLAGS)):
				errors.append("sector %s: dance is only for dance_floor or stage sectors, and never in the quiet band" % sid)
			else:
				names.append(str(n))
		out[str(band)] = names
	for band in ["quiet", "dancing", "hype"]:
		if not out.has(band) or (out[band] as Array).is_empty():
			errors.append("sector %s: activities needs a non-empty list for the %s band" % [sid, band])
	if not out.has("euphoric") or (out["euphoric"] as Array).is_empty():
		out["euphoric"] = out.get("hype", [])
	out["authored"] = true
	return out


static func _any_in(a: Array, b: Array) -> bool:
	for x in a:
		if x in b:
			return true
	return false


static func default_activities(flags: Array) -> Dictionary:
	if _any_in(flags, DANCE_FLAGS):
		return {"quiet": ["stand", "chat", "drink", "phone", "lean_wall"], "dancing": ["dance", "dance", "dance", "drink", "chat"], "hype": ["dance", "dance", "dance", "wave", "point"],
			"euphoric": ["dance", "dance", "wave", "point"]}
	return {"quiet": ["stand", "chat", "lean_wall"], "dancing": ["stand", "chat", "watch", "drink"], "hype": ["watch", "wave", "chat"], "euphoric": ["wave", "watch", "chat"]}


## The activities a person standing in sector `sid` may pick at an energy band (euphoric falls back to hype).
func activities_of(sid: String, band: String) -> Array:
	var acts: Dictionary = sector(sid).get("activities", {})
	if acts.is_empty():
		acts = default_activities(sector(sid).get("flags", []))
	var l: Array = acts.get(band, [])
	return l if not l.is_empty() else acts.get("hype", ["stand"])


static func _signed_area(p: PackedVector2Array) -> float:
	var a := 0.0
	for i in p.size():
		var q := p[(i + 1) % p.size()]
		a += p[i].x * q.y - q.x * p[i].y
	return a * 0.5


func _check_polygon(sid: String, p: PackedVector2Array) -> void:
	var n := p.size()
	for i in n:
		if p[i].distance_to(p[(i + 1) % n]) < EPS:
			errors.append("sector %s: repeated point" % sid)
			return
	for i in n:
		for j in range(i + 1, n):
			if j == i + 1 or (i == 0 and j == n - 1):
				continue
			if Geometry2D.segment_intersects_segment(p[i], p[(i + 1) % n], p[j], p[(j + 1) % n]) != null:
				errors.append("sector %s: the polygon is not simple (edges %d and %d meet)" % [sid, i, j])
				return
	if absf(_signed_area(p)) < 0.01:
		errors.append("sector %s: the polygon has no area" % sid)
		return
	var sign := 0
	for i in n:
		var c := (p[(i + 1) % n] - p[i]).cross(p[(i + 2) % n] - p[(i + 1) % n])
		if absf(c) < EPS:
			continue
		var sg := 1 if c > 0.0 else -1
		if sign != 0 and sg != sign:
			errors.append("sector %s: the polygon is not convex (split it into sectors; rail pathing needs convex rooms)" % sid)
			return
		sign = sg


func _check_overlap(a: Dictionary, b: Dictionary) -> void:
	var pa: PackedVector2Array = a["poly"]
	var pb: PackedVector2Array = b["poly"]
	if pa.size() < 3 or pb.size() < 3:
		return
	var bad := false
	for piece in Geometry2D.intersect_polygons(pa, pb):  # shared edges give no area; any real overlap does
		if absf(_signed_area(piece)) > 0.01:
			bad = true
	if bad:
		errors.append("sectors %s and %s overlap" % [a["id"], b["id"]])


static func _dist_to_segment(p: Vector2, a: Vector2, b: Vector2) -> float:
	return p.distance_to(Geometry2D.get_closest_point_to_segment(p, a, b))


static func _dist_to_boundary(p: Vector2, poly: PackedVector2Array) -> float:
	var best := INF
	for i in poly.size():
		best = minf(best, _dist_to_segment(p, poly[i], poly[(i + 1) % poly.size()]))
	return best


## The polygon edge index that holds both a and b (within EPS), or -1.
static func edge_holding(a: Vector2, b: Vector2, poly: PackedVector2Array) -> int:
	for i in poly.size():
		var p := poly[i]
		var q := poly[(i + 1) % poly.size()]
		if _dist_to_segment(a, p, q) < EPS and _dist_to_segment(b, p, q) < EPS:
			return i
	return -1


func _build_walls(list: Array) -> void:
	var seen_portals := {}
	for w in list:
		var sid := str(w.get("sector", ""))
		var where := "wall in %s" % sid
		if not _sector_index.has(sid):
			errors.append("%s: unknown sector" % where)
			continue
		var a := _pt(w.get("from"), where)
		var b := _pt(w.get("to"), where)
		var poly: PackedVector2Array = sectors[_sector_index[sid]]["poly"]
		if a.distance_to(b) < 0.05:
			errors.append("%s: zero length" % where)
			continue
		if poly.size() >= 3 and edge_holding(a, b, poly) < 0:
			errors.append("%s: %s to %s is not on one edge of the sector" % [where, a, b])
			continue
		var portal := "" if w.get("portal") == null else str(w["portal"])
		if portal != "":
			if not _sector_index.has(portal) or portal == sid:
				errors.append("%s: portal to %s has no sector on the other side" % [where, portal])
				continue
			var opoly: PackedVector2Array = sectors[_sector_index[portal]]["poly"]
			if opoly.size() >= 3 and edge_holding(a, b, opoly) < 0:
				errors.append("%s: the portal to %s does not lie on one of its edges" % [where, portal])
				continue
			var key := [sid, portal]
			key.sort()
			seen_portals[str(key)] = seen_portals.get(str(key), []) + [[a, b]]
		var tex := str(w.get("tex", ""))
		for k in ["tex", "lower_tex", "upper_tex"]:
			_tex_ok(str(w.get(k, "")), where)
		_walls_in.append({"a": a, "b": b, "sector": sid, "portal": portal, "tex": tex, "lower_tex": str(w.get("lower_tex", "")), "upper_tex": str(w.get("upper_tex", "")), "blocked": bool(w.get("blocked", false)) and portal != ""})
	# a portal is declared once (the other sector sees it implicitly)
	for k in seen_portals:
		var segs: Array = seen_portals[k]
		for i in segs.size():
			for j in range(i + 1, segs.size()):
				if _overlap_len(segs[i][0], segs[i][1], segs[j][0], segs[j][1]) > EPS:
					errors.append("portal %s is declared twice" % k)
	for i in _walls_in.size():
		for j in range(i + 1, _walls_in.size()):
			var wi: Dictionary = _walls_in[i]
			var wj: Dictionary = _walls_in[j]
			if wi["sector"] == wj["sector"] and _overlap_len(wi["a"], wi["b"], wj["a"], wj["b"]) > EPS:
				errors.append("walls %d and %d of sector %s overlap" % [i, j, wi["sector"]])


static func _overlap_len(a: Vector2, b: Vector2, c: Vector2, d: Vector2) -> float:
	var dir := b - a
	var l := dir.length()
	if l < EPS:
		return 0.0
	dir /= l
	if absf((c - a).cross(dir)) > EPS or absf((d - a).cross(dir)) > EPS:
		return 0.0
	var t0 := (c - a).dot(dir)
	var t1 := (d - a).dot(dir)
	return maxf(0.0, minf(l, maxf(t0, t1)) - maxf(0.0, minf(t0, t1)))


func _build_things(list: Array) -> void:
	var seen := {}
	for t in list:
		var tid := str(t.get("id", ""))
		var sid := str(t.get("sector", ""))
		var at := _pt(t.get("at"), "thing " + tid)
		if sid == "":  # a thing names no sector: it belongs to the sector that holds it
			sid = sector_at(at)
		if tid == "" or seen.has(tid):
			errors.append("thing id %s missing or duplicated" % tid)
			continue
		seen[tid] = true
		if str(t.get("kind", "billboard")) == "light":
			_build_light(t, tid, sid, at)
			continue
		if not _sector_index.has(sid):
			errors.append("thing %s: lies in no sector" % tid)
			continue
		var poly: PackedVector2Array = sectors[_sector_index[sid]]["poly"]
		if poly.size() >= 3 and not Geometry2D.is_point_in_polygon(at, poly):
			errors.append("thing %s: %s is not inside sector %s" % [tid, at, sid])
		if str(t.get("sprite", "")) == "":
			errors.append("thing %s: no sprite" % tid)
		if str(t.get("anim", "none")) not in ANIMS:
			errors.append("thing %s: unknown anim %s" % [tid, t.get("anim")])
		if float(t.get("size", 1.0)) <= 0.0:
			errors.append("thing %s: size must be positive" % tid)
		var th: Dictionary = t.duplicate()
		th["sector"] = sid
		th["at"] = at
		things.append(th)


## A light thing: {"id", "kind": "light", "at": [x, z], "y": metres above the floor (default 2.4), "radius": m, "color": "#hex", "strength": 0..2.5 (default 1),
## "cone": {"yaw": degrees (0 looks toward -z), "angle": half angle degrees} (a window's shape across the floor, a doorway's spill), "sectors": [ids it reaches] (default: its own sector and the
## ones next to it through a portal)}.
func _build_light(t: Dictionary, tid: String, sid: String, at: Vector2) -> void:
	if not _sector_index.has(sid):
		errors.append("light %s: lies in no sector" % tid)
		return
	var poly: PackedVector2Array = sectors[_sector_index[sid]]["poly"]
	if poly.size() >= 3 and not Geometry2D.is_point_in_polygon(at, poly):
		errors.append("light %s: %s is not inside sector %s" % [tid, at, sid])
	var radius := float(t.get("radius", 4.0))
	var strength := float(t.get("strength", 1.0))
	if radius <= 0.1 or radius > 30.0:
		errors.append("light %s: radius is 0.1 to 30 m" % tid)
	if strength < 0.0 or strength > 2.5:
		errors.append("light %s: strength is 0 to 2.5" % tid)
	var l := {"id": tid, "sector": sid, "at": at, "y": float(t.get("y", 2.4)), "radius": radius, "strength": strength, "color": Color.html(str(t.get("color", "#ffffff")))}
	if t.has("cone"):
		var c: Dictionary = t["cone"]
		l["cone"] = {"yaw": float(c.get("yaw", 0.0)), "angle": clampf(float(c.get("angle", 40.0)), 5.0, 89.0)}
	if t.has("sectors"):
		for k in t["sectors"]:
			if not _sector_index.has(str(k)):
				errors.append("light %s: reaches unknown sector %s" % [tid, k])
		l["sectors"] = t["sectors"]
	lights.append(l)


func _inside(p: Vector2, sid: String, margin: float) -> bool:
	if not _sector_index.has(sid):
		return false
	var poly: PackedVector2Array = sectors[_sector_index[sid]]["poly"]
	return poly.size() >= 3 and Geometry2D.is_point_in_polygon(p, poly) and _dist_to_boundary(p, poly) >= margin - 1.0e-6


func _build_waypoints(list: Array) -> void:
	for w in list:
		var wid := str(w.get("id", ""))
		var at := _pt(w.get("at"), "waypoint " + wid)
		var sid := str(w.get("sector", ""))
		if wid == "" or waypoints.has(wid):
			errors.append("waypoint id %s missing or duplicated" % wid)
			continue
		if not _sector_index.has(sid):
			errors.append("waypoint %s: unknown sector %s" % [wid, sid])
			continue
		if not _inside(at, sid, WAYPOINT_MARGIN):
			errors.append("waypoint %s: %s is not inside sector %s (with a %.1f m margin)" % [wid, at, sid, WAYPOINT_MARGIN])
		waypoints[wid] = {"at": at, "yaw": float(w.get("yaw", 0.0)), "sector": sid}


## True when ground point p lies inside sector sid with at least `margin` metres to its walls.
func inside(p: Vector2, sid: String, margin := 0.0) -> bool:
	return _inside(p, sid, margin)


func _build_homes(list: Array) -> void:
	for h in list:
		var aid := str(h.get("actor", ""))
		var sid := str(h.get("sector", ""))
		var at := _pt(h.get("at"), "home " + aid)
		if aid == "" or homes.has(aid):
			errors.append("home for actor %s missing or duplicated" % aid)
			continue
		if not _sector_index.has(sid):
			errors.append("home %s: unknown sector %s" % [aid, sid])
			continue
		if not _inside(at, sid, HOME_MARGIN):
			errors.append("home %s: %s is not inside sector %s (with a %.2f m margin from the walls)" % [aid, at, sid, HOME_MARGIN])
		var entry := {"sector": sid, "at": at}
		if h.has("side"):  # where a dancer who stays on a bad night waits at the edge of the floor
			var side := _pt(h["side"], "home %s side" % aid)
			if not _inside(side, sid, HOME_MARGIN):
				errors.append("home %s: side spot %s is not inside sector %s" % [aid, side, sid])
			entry["side"] = side
		homes[aid] = entry


func _build_spots(d: Variant) -> void:
	if typeof(d) != TYPE_DICTIONARY:
		return
	for name in d:
		var sp: Dictionary = d[name]
		var sid := str(sp.get("sector", ""))
		var at := _pt(sp.get("at"), "spot " + str(name))
		if not _sector_index.has(sid):
			errors.append("spot %s: unknown sector %s" % [name, sid])
			continue
		if not _inside(at, sid, HOME_MARGIN):
			errors.append("spot %s: %s is not inside sector %s" % [name, at, sid])
		var e := {"sector": sid, "at": at}
		if sp.has("slots"):  # door: where the people waiting outside stand (indexed by an actor's door_slot)
			var slots: Array = []
			for k in (sp["slots"] as Array):
				var q := _pt(k, "spot %s slot" % name)
				if not _inside(q, sid, HOME_MARGIN):
					errors.append("spot %s: slot %s is not inside sector %s" % [name, q, sid])
				slots.append(q)
			e["slots"] = slots
		if sp.has("radii"):  # circle: x and z radii (m), the circle stays inside its sector
			var r: Array = sp["radii"]
			if r.size() != 2 or float(r[0]) <= 0.0 or float(r[1]) <= 0.0:
				errors.append("spot %s: radii are [rx, rz] in metres" % name)
			else:
				e["radii"] = Vector2(float(r[0]), float(r[1]))
				for k in 16:
					var ang := TAU * float(k) / 16.0
					var pt := at + Vector2(cos(ang) * float(r[0]), sin(ang) * float(r[1]))
					if not _inside(pt, sid, HOME_MARGIN):
						errors.append("spot %s: the circle leaves sector %s at %s" % [name, sid, pt])
						break
		if sp.has("open"):
			var o: Array = sp["open"]
			e["open"] = Vector2(float(o[0]), float(o[1])).normalized() if o.size() == 2 else Vector2(0, -1)
		spots[str(name)] = e


func _build_silhouettes(list: Variant) -> void:
	if typeof(list) != TYPE_ARRAY:
		return
	for s in list:
		var sid_ := str(s.get("id", ""))
		var at := _pt(s.get("at"), "silhouette " + sid_)
		var sec := sector_at(at)
		if sid_ == "" or silhouettes.has(sid_) or sec == "":
			errors.append("silhouette %s: missing, duplicated or outside every sector" % sid_)
			continue
		silhouettes[sid_] = {"sector": sec, "at": at}


func spot(name: String) -> Dictionary:
	return spots.get(name, {})


func _build_occluders(list: Array) -> void:
	for o in list:
		var oid := str(o.get("id", ""))
		if oid == "" or str(o.get("sprite", "")) == "":
			errors.append("occluder %s: needs an id and a sprite" % oid)
			continue
		var oc: Dictionary = o.duplicate()
		if o.has("between"):  # a frame the camera passes through between two sectors (placed on their shared portal when no `at` is given)
			var between: Array = o["between"]
			if between.size() != 2 or not _sector_index.has(str(between[0])) or not _sector_index.has(str(between[1])):
				errors.append("occluder %s: between needs two existing sectors" % oid)
				continue
			if not o.has("at"):
				for p in portals():
					if (p["a"] == between[0] and p["b"] == between[1]) or (p["a"] == between[1] and p["b"] == between[0]):
						oc["at"] = p["mid"]
						oc["sector"] = str(between[0])
						break
		if not oc.has("at"):
			errors.append("occluder %s: needs `at` (or a portal `between` two sectors)" % oid)
			continue
		var at: Variant = oc["at"]
		at = at if typeof(at) == TYPE_VECTOR2 else _pt(at, "occluder " + oid)
		oc["at"] = at
		var sec := str(oc.get("sector", sector_at(at)))
		if sec == "" or not _sector_index.has(sec):
			errors.append("occluder %s: lies in no sector" % oid)
			continue
		oc["sector"] = sec
		if not textures.has(str(o["sprite"])):
			errors.append("occluder %s: sprite %s is not one of the map's textures" % [oid, o["sprite"]])
		oc["width"] = float(o.get("width", 1.0))
		oc["height"] = float(o.get("height", 2.0))
		occluders.append(oc)


# --- portals, reachability, resolved walls ---------------------------------------------------------------------------------------------

func _collect_portals() -> void:
	_portals = []
	for w in _walls_in:
		if str(w["portal"]) != "":
			_portals.append({"a": str(w["sector"]), "b": str(w["portal"]), "p0": w["a"], "p1": w["b"], "mid": (w["a"] + w["b"]) * 0.5, "blocked": bool(w.get("blocked", false))})


func portals() -> Array:
	if _portals.is_empty():
		_collect_portals()
	return _portals


## The sectors a walker can step into from `sid`: through the portals that are not `blocked` (a blocked portal is an opening to look through, a balcony rail or a window,
## that nobody walks across: it still shows the other room and the crowd in it).
## The lights that reach sector `sid`: those in it, those listing it, and those in a sector next to it through a portal (a doorway spills into the corridor behind it).
func lights_reaching(sid: String) -> Array:
	var out: Array = []
	var near: Array = [sid]
	for p in portals():
		if p["a"] == sid:
			near.append(p["b"])
		elif p["b"] == sid:
			near.append(p["a"])
	for l in lights:
		if l.has("sectors"):
			if sid in l["sectors"] or sid == l["sector"]:
				out.append(l)
		elif str(l["sector"]) in near:
			out.append(l)
	return out


func neighbors(sid: String) -> Array:
	var out: Array = []
	for p in portals():
		if bool(p["blocked"]):
			continue
		if p["a"] == sid and not out.has(p["b"]):
			out.append(p["b"])
		elif p["b"] == sid and not out.has(p["a"]):
			out.append(p["a"])
	return out


func reachable_from(sid: String) -> Dictionary:
	var seen := {sid: true}
	var queue := [sid]
	while not queue.is_empty():
		var s: String = queue.pop_front()
		for n in neighbors(s):
			if not seen.has(n):
				seen[n] = true
				queue.append(n)
	return seen


func _check_reachability() -> void:
	if not waypoints.has(start_id) or sectors.is_empty():
		return
	var seen := reachable_from(str(waypoints[start_id]["sector"]))
	for s in sectors:
		if not seen.has(s["id"]):
			errors.append("sector %s cannot be reached from the start waypoint through portals" % s["id"])


## Every wall as drawn: the explicit ones, each portal's implicit mirror in the sector on the other side, and default walls (the sector's
## wall_tex) over every stretch of a polygon edge that nothing else covers. {a, b (Vector2), sector, portal ("" for solid), tex, lower_tex,
## upper_tex}; a and b run along the sector's counter-clockwise edge direction, so the room is on the left of a to b.
func resolved_walls() -> Array:
	return _walls_out


func _resolve_walls() -> void:
	_walls_out = []
	var all: Array = []
	for w in _walls_in:
		all.append(w)
		if str(w["portal"]) != "":
			all.append({"a": w["b"], "b": w["a"], "sector": w["portal"], "portal": w["sector"], "tex": w["tex"], "lower_tex": w["lower_tex"], "upper_tex": w["upper_tex"], "implicit": true})
	for s in sectors:
		var poly: PackedVector2Array = s["poly"]
		for i in poly.size():
			var p := poly[i]
			var q := poly[(i + 1) % poly.size()]
			var len := p.distance_to(q)
			var dir := (q - p) / len
			var pieces: Array = []  # [t0, t1, wall]
			for w in all:
				if w["sector"] != s["id"] or edge_holding(w["a"], w["b"], PackedVector2Array([p, q])) != 0:
					continue
				var t0: float = ((w["a"] as Vector2) - p).dot(dir)
				var t1: float = ((w["b"] as Vector2) - p).dot(dir)
				var nw: Dictionary = (w as Dictionary).duplicate()
				nw["a"] = p + dir * minf(t0, t1)
				nw["b"] = p + dir * maxf(t0, t1)
				pieces.append([minf(t0, t1), maxf(t0, t1), nw])
			pieces.sort_custom(func(x: Array, y: Array) -> bool: return x[0] < y[0])
			var at := 0.0
			for pc in pieces:
				if float(pc[0]) > at + EPS:
					_walls_out.append(_default_wall(s, p + dir * at, p + dir * float(pc[0])))
				_walls_out.append(pc[2])
				at = maxf(at, float(pc[1]))
			if at < len - EPS:
				_walls_out.append(_default_wall(s, p + dir * at, q))
	for w in _walls_out:  # unset textures fall back to the sector's own
		var sec: Dictionary = sectors[_sector_index[w["sector"]]]
		if str(w["tex"]) == "":
			w["tex"] = str(sec["wall_tex"])
		if str(w["lower_tex"]) == "":
			w["lower_tex"] = str(w["tex"])
		if str(w["upper_tex"]) == "":
			w["upper_tex"] = str(w["tex"])


func _default_wall(s: Dictionary, a: Vector2, b: Vector2) -> Dictionary:
	return {"a": a, "b": b, "sector": s["id"], "portal": "", "tex": str(s["wall_tex"]), "lower_tex": "", "upper_tex": "", "auto": true}


# --- queries -------------------------------------------------------------------------------------------------------------------------------

func sector(sid: String) -> Dictionary:
	return sectors[_sector_index[sid]] if _sector_index.has(sid) else {}


## The sector holding the ground point p ("" when outside every sector).
func sector_at(p: Vector2) -> String:
	for s in sectors:
		var poly: PackedVector2Array = s["poly"]
		if poly.size() >= 3 and (Geometry2D.is_point_in_polygon(p, poly) or _dist_to_boundary(p, poly) < EPS):
			return str(s["id"])
	return ""


## The room (a view of the chapter: "main", "gallery"...) a sector belongs to.
func room_of(sid: String) -> String:
	return str(sector(sid).get("room", "main"))


## The rooms that hold actors or silhouettes of the chapter: the crowd views. "main" always.
static func crowd_rooms(chapter_raw: Dictionary) -> Array:
	var out: Array = ["main"]
	for key in ["actors", "silhouettes"]:
		for a in chapter_raw.get(key, []):
			var v := str(a.get("view", "main"))
			if v not in out:
				out.append(v)
	return out


## A named place of a room: "<room>.<name>" first (the gallery's own door), then the plain name (the main room's).
func room_spot(room: String, name: String) -> Dictionary:
	if room != "main" and spots.has("%s.%s" % [room, name]):
		return spots["%s.%s" % [room, name]]
	return spots.get(name, {})


func waypoint(wid: String) -> Dictionary:
	return waypoints.get(wid, {})


## The room ids of the map's sectors.
func rooms_list() -> Array:
	var out: Array = []
	for s in sectors:
		if str(s["room"]) not in out:
			out.append(str(s["room"]))
	return out


func has_waypoint(wid: String) -> bool:
	return waypoints.has(wid)


func home(actor: String) -> Dictionary:
	return homes.get(actor, {})


func start_waypoint() -> Dictionary:
	return waypoints.get(start_id, {})


## Eye height above the world floor for a point in sector sid.
func eye_y(sid: String) -> float:
	return float(sector(sid).get("floor", 0.0)) + eye_height


func forward_of_yaw(yaw_deg: float) -> Vector2:
	var r := deg_to_rad(yaw_deg)
	return Vector2(-sin(r), -cos(r))


## A* over the portal graph. The route runs from `from` (in sector `from_sec`) through the midpoint of each portal crossed to `to`.
## Returns {points: PackedVector2Array (start, portal midpoints, end), sectors: Array (the sector each leg lies in), length}.
## Because every sector is convex, each leg stays inside its sector. An empty `points` means no route.
func route(from: Vector2, from_sec: String, to: Vector2, to_sec: String) -> Dictionary:
	var none := {"points": PackedVector2Array(), "sectors": [], "length": 0.0}
	if not _sector_index.has(from_sec) or not _sector_index.has(to_sec):
		return none
	var ps := portals()
	var n := 2 + ps.size()
	var pos: Array = [from, to]
	var secs: Array = [[from_sec], [to_sec]]
	for p in ps:
		pos.append(p["mid"])
		secs.append([p["a"], p["b"]] if not bool(p["blocked"]) else ["", ""])  # a blocked portal joins nothing for a walker
	var g := {0: 0.0}
	var prev := {}
	var open: Array = [0]
	var closed := {}
	while not open.is_empty():
		var best := 0
		for i in open.size():  # lowest f, ties by node index: deterministic
			var fi: float = g[open[i]] + (pos[open[i]] as Vector2).distance_to(to)
			var fb: float = g[open[best]] + (pos[open[best]] as Vector2).distance_to(to)
			if fi < fb - 1.0e-9 or (absf(fi - fb) <= 1.0e-9 and open[i] < open[best]):
				best = i
		var cur: int = open.pop_at(best)
		if cur == 1:
			break
		closed[cur] = true
		for nb in n:
			if nb == cur or closed.has(nb) or (cur == 0 and nb == 1 and from_sec != to_sec):
				continue
			var shared := ""
			for s in secs[cur]:
				if s in secs[nb]:
					shared = s
					break
			if shared == "":
				continue
			var cost: float = g[cur] + (pos[cur] as Vector2).distance_to(pos[nb])
			if not g.has(nb) or cost < g[nb] - 1.0e-9:
				g[nb] = cost
				prev[nb] = [cur, shared]
				if nb not in open:
					open.append(nb)
	if not prev.has(1):
		return none
	var chain: Array = []
	var node := 1
	while node != 0:
		chain.push_front(node)
		node = int(prev[node][0])
	var pts := PackedVector2Array([from])
	var legs: Array = []
	var last := 0
	for c in chain:
		pts.append(pos[c])
		legs.append(str(prev[c][1]))
		last = c
	return {"points": pts, "sectors": legs, "length": float(g[1])}


## The sectors that can be seen from `cam` (a ground point in sector `sec`) looking along `yaw` (degrees) through a window of `aspect` (width / height) at the
## projector's vertical field of view: the camera's own sector (depth 0) and the sectors beyond portals whose opening lies in view, up to `max_depth` portals deep.
## Returns {sector id: portal depth}. A generous margin keeps a dancer in the doorway from popping.
func visible_sectors(cam: Vector2, yaw: float, sec: String, aspect: float, max_depth := 4) -> Dictionary:
	var out := {}
	if not _sector_index.has(sec):
		return out
	out[sec] = 0
	var half := atan(tan(deg_to_rad(StoryProjector.FOV_V) * 0.5) * aspect) + deg_to_rad(8.0)
	var fwd := StoryProjector.forward(yaw)
	var rgt := StoryProjector.right(yaw)
	var frontier := [sec]
	for depth in range(1, max_depth + 1):
		var next: Array = []
		for cur in frontier:
			for p in portals():
				var other := ""
				if p["a"] == cur:
					other = str(p["b"])
				elif p["b"] == cur:
					other = str(p["a"])
				if other == "" or out.has(other):
					continue
				if _portal_in_view(cam, fwd, rgt, p["p0"], p["p1"], half):
					out[other] = depth
					next.append(other)
		frontier = next
	return out


func _portal_in_view(cam: Vector2, fwd: Vector2, rgt: Vector2, p0: Vector2, p1: Vector2, half: float) -> bool:
	var a := Vector2((p0 - cam).dot(rgt), (p0 - cam).dot(fwd))  # (right, depth)
	var b := Vector2((p1 - cam).dot(rgt), (p1 - cam).dot(fwd))
	var near := 0.05
	if a.y < near and b.y < near:
		return false
	if a.y < near:
		a = a.lerp(b, (near - a.y) / (b.y - a.y))
	elif b.y < near:
		b = b.lerp(a, (near - b.y) / (a.y - b.y))
	var ang_a := atan2(a.x, a.y)
	var ang_b := atan2(b.x, b.y)
	return minf(ang_a, ang_b) <= half and maxf(ang_a, ang_b) >= -half


# --- the chapter's own references ------------------------------------------------------------------------------------------------------

## Every authored player_move / player_look in a chapter file (events, `else` alternatives and decision outcomes):
## [{action, args, where}].
static func journey_actions(chapter_raw: Dictionary) -> Array:
	var out: Array = []
	for b in chapter_raw.get("blocks", []):
		for e in b.get("events", []):
			for key in ["action", "else"]:
				var an := str(e.get(key, ""))
				if an.begins_with("player_"):
					out.append({"action": an, "args": e, "where": "%s bar %s" % [b.get("id", "?"), e.get("at_bar", "?")]})
	for d in chapter_raw.get("decisions", []):
		for outcome in ["good", "bad"]:
			for a in d.get(outcome, []):
				if typeof(a) == TYPE_DICTIONARY and str(a.get("action", "")).begins_with("player_"):
					out.append({"action": str(a["action"]), "args": a, "where": "decision %s %s" % [d.get("id", "?"), outcome]})
	var ends: Variant = chapter_raw.get("endings", {})
	if typeof(ends) == TYPE_DICTIONARY:
		for key in ends:
			for a in (ends[key] as Dictionary).get("journey", []):
				if typeof(a) == TYPE_DICTIONARY and str(a.get("action", "")).begins_with("player_"):
					out.append({"action": str(a["action"]), "args": a, "where": "ending %s" % key})
	return out


## Chapter-level rules: every actor has a home (and every home an actor), every player_move target is a waypoint, player_look targets are
## waypoints or actors, styles and roles are known. Errors are appended to `errors`.
func validate_chapter(chapter_raw: Dictionary) -> void:
	var actor_ids := {}
	for a in chapter_raw.get("actors", []):
		actor_ids[str(a["id"])] = true
		if not homes.has(str(a["id"])):
			errors.append("actor %s has no home in the map" % a["id"])
	for sil in chapter_raw.get("silhouettes", []):
		if not silhouettes.has(str(sil["id"])):
			errors.append("silhouette %s has no place in the map" % sil["id"])
	for a in chapter_raw.get("actors", []):
		if str(a.get("group", "")) == "gatherers" and str(a.get("enter_from", "doorway")) == "doorway":
			var slots: Array = spot("door").get("slots", [])
			if not slots.is_empty() and int(a.get("door_slot", 0)) >= slots.size():
				errors.append("actor %s: door_slot %s but the door has %d slots" % [a["id"], a.get("door_slot"), slots.size()])
	for h in homes:
		if not actor_ids.has(h):
			errors.append("home %s is not an actor of the chapter" % h)
	for ja in journey_actions(chapter_raw):
		var args: Dictionary = ja["args"]
		match str(ja["action"]):
			"player_move":
				if not waypoints.has(str(args.get("to", ""))):
					errors.append("%s: player_move to %s is not a waypoint" % [ja["where"], args.get("to", "")])
				if str(args.get("style", "walk")) not in MOVE_STYLES:
					errors.append("%s: unknown move style %s" % [ja["where"], args.get("style")])
			"player_walk":
				for key in ["to", "face"]:
					var tgt := str(args.get(key, ""))
					if tgt != "" and not waypoints.has(tgt) and not actor_ids.has(tgt):
						errors.append("%s: player_walk %s %s is neither a waypoint nor an actor" % [ja["where"], key, tgt])
				if str(args.get("to", "")) == "" and not args.has("fwd") and not args.has("right"):
					errors.append("%s: player_walk needs `to` or fwd / right" % ja["where"])
				if str(args.get("style", "walk")) not in MOVE_STYLES:
					errors.append("%s: unknown walk style %s" % [ja["where"], args.get("style")])
				var inr: Variant = args.get("in", [])
				for room in (inr if typeof(inr) == TYPE_ARRAY else [inr]):
					if not rooms_list().has(str(room)) and not _sector_index.has(str(room)):
						errors.append("%s: player_walk in %s is neither a room nor a sector of the map" % [ja["where"], room])
			"player_look":
				var at := str(args.get("at", ""))
				if at != "" and not waypoints.has(at) and not actor_ids.has(at):
					errors.append("%s: player_look at %s is neither a waypoint nor an actor" % [ja["where"], at])
				var look_in: Variant = args.get("in", [])
				for room2 in (look_in if typeof(look_in) == TYPE_ARRAY else [look_in]):
					if not rooms_list().has(str(room2)) and not _sector_index.has(str(room2)):
						errors.append("%s: player_look in %s is neither a room nor a sector of the map" % [ja["where"], room2])
				if at == "" and not args.has("yaw") and not args.has("by") and not args.has("pitch"):
					errors.append("%s: player_look needs yaw, at, by or pitch" % ja["where"])
			"player_role":
				if str(args.get("role", "")) not in ROLES:
					errors.append("%s: unknown role %s" % [ja["where"], args.get("role", "")])
