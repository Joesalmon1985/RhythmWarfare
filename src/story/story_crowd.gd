class_name StoryCrowd
extends Node2D
## One room's crowd in the 2.5D world: rigged dancers (StoryCharacter) and cheap rear silhouettes standing at the map's homes, projected through the player's
## camera, sorted by distance and driven by the crowd energy plus authored directives. Everything is a pure function of song time and
## the (deterministic) actions the director emits, so it pauses, restarts and fast-forwards exactly.
##
## Per dancer the state is: walking (arrival/exit), else an active directive (clap, cheer, look, ...), else the mood from the
## crowd energy plus the dancer's own threshold (so they react at different levels): sad < idle < dance < cheer.

const SIL_UP_E := 66.0
const NO_END := 1.0e9

var assets: StoryAssets
var view := "main"  # the room this crowd lives in (actors and silhouettes with that `view`)
var data: StoryData
var bpm := 174.0
var reduced := false
var energy := 45.0
var glow_on := false
var lit_id := ""  # the dancer a followspot is on (drawn a touch brighter)
const STORY_LIT := 1.25  # the light on a person a hotspot directs
var actors: Dictionary = {}  # id -> {node, data, home: Vector2, pos: Vector2, present, depth, move: {}, dir: {}, thresh, scale}
var _order: Array = []
var _sils: Array = []
var _rng := RandomNumberGenerator.new()
var door_pos := Vector2.ZERO
var circle_c := Vector2.ZERO
var circle_r := Vector2(3.0, 1.8)
var _ending := ""
var _flinch_until := -1.0
var glow_colors: Array = [Color(0.4, 1.0, 0.95), Color(1.0, 0.4, 0.85), Color(1.0, 0.8, 0.3)]

## The 2.5D world (StoryMap, docs/STORY_25D_PLAN.md): with a map attached positions are ground coordinates [x, z] in metres instead of design pixels, every
## actor's feet are projected through StoryProjector from the camera pose the stage hands over, dancers are sorted by distance and culled by sector visibility.
const HERO_M := 1.7  # a dancer is this tall in the world
## The figure size cap (style guide section 7, audit F1(b) and F8): a person is never drawn larger than FIG_CAP internal pixels per pixel of the finest level of their
## sheet (`mag`). Coming closer, a person of the crowd dissolves (an ordered-dither fade, story_people.gdshader) between FIG_FADE and FIG_CAP and is gone at the cap;
## a person the story needs (the hero, the followspot's dancer, anyone acting for a hotspot or its outcome, anyone directed) is held back instead: drawn on the floor at the
## cap distance along their own bearing, so they stay whole and readable. A bigger finest level (people.json `h0` / min `lods`) moves the cap closer by itself.
const FIG_CAP := 1.25
const FIG_FADE := 1.05
const SIL_NEAR_M := 8.0
const OPEN_GAP := 0.42
const POSE_RATE := 30.0
const POSE_RATE_FAR := 15.0  # dancers further than FAR_M animate at this rate: they are a few pixels tall
const FAR_M := 9.0
var map: StoryMap
var world_mode := false
var cam_pose: Dictionary = {}  # {cam: Vector3, yaw}
var view_size := Vector2(480, 170)
var vis_sectors: Dictionary = {}  # sector id -> portal depth, from StoryMap.visible_sectors; empty = everything visible
var tint_fn := Callable()  # sector id -> Color, the light a prop is seen in
var circle_open := Vector2(0, -1)
var riser_spot := Vector2.ZERO
var floor_x := Vector2(-6.5, 6.5)  # the dance floor's x range, for waves
var door_slots: Array = []
var props: Array = []  # StoryCrowdProp nodes (silhouettes and occluders)
var _room_sectors: Array = []  # the sector ids of this crowd's room
var _room_visible := true  # false while no sector of the room can be seen: the crowd then only keeps its walks, fades and arrivals (no projection, mood or pose)
var drawn := 0  # actors drawn last frame (a probe for the tests and the profiler)
var _pose_key := ""
var _order_key := ""


var people: StoryPeople  # the chapter's baked sheets (null: the live rig draws everyone)
var light_fn := Callable()  # (sector id, ground position) -> Color: the light a person stands in (the stage sets it when the world is built)
var fog_m := Vector2(5.5, 17.0)  # depth (m) where the back rows start fading into the fog, and where they are fully faded
var fig_m := 112.0 / HERO_M  # sheet pixels per metre of the finest level (setup reads the chapter's sheets)
var cap_max := 0.0  # the largest `mag` drawn last frame (the headless figure-cap check reads it)
var cap_over := 0  # people drawn above FIG_CAP last frame (must stay 0)
var cap_held := 0  # people held back at the cap last frame
var cap_gone := 0  # crowd people inside the cap last frame (dissolved away)


func setup(p_assets: StoryAssets, p_data: StoryData) -> void:
	assets = p_assets
	data = p_data
	_rng.seed = 4242
	people = StoryPeople.for_assets(assets)
	if people != null and people.ok():
		var lmin := 1.0
		for l in people.lods:
			lmin = minf(lmin, float(l))
		fig_m = people.h0 / maxf(lmin, 0.01) / HERO_M
	var n := 0
	for a in data.actors:
		if str(a.get("view", "main")) != view:
			continue
		var rig := assets.rig(str(a["archetype"]), str(a["variant"]), str(a.get("art", "")))
		if rig.is_empty():
			continue
		var c := StoryCharacter.new()
		c.name = str(a["id"])
		c.setup(assets, rig, str(a["id"]), 1000 + n)
		c.glow = bool(a.get("glow", false)) or (n % 4 == 0)
		c.glow_color = glow_colors[n % glow_colors.size()]
		add_child(c)
		var present := str(a["group"]) == "core"
		c.held = str(a.get("prop", "")) if str(a.get("prop", "")) in StoryCharacter.PROPS and str(a.get("activity", "")) != "" else ""
		if people != null and people.ok() and not people.entry(str(a["id"])).is_empty():
			c.attach_sheet(people, people.entry(str(a["id"])))
		var fl := flair_of(str(a["id"])) if str(a.get("activity", "")) == "" and str(a.get("role", "")) != "hero" else ""
		if fl != "" and not (c.uses_sheet() and (c.sheet.get("states", {}) as Dictionary).has(fl)):
			fl = ""  # only a person whose sheet carries the move performs it (the live rig cannot crouch)
		actors[str(a["id"])] = {"node": c, "data": a, "seed": _id_seed(str(a["id"])), "flair": fl, "lock": str(a.get("activity", "")), "partner": "", "act": "", "home": Vector2.ZERO, "pos": Vector2.ZERO, "present": present, "move": {}, "dir": {},
			"thresh": float(a.get("thresh", 0.0)), "alpha": 1.0 if present else 0.0, "stay": false, "vanish": {}}
		n += 1
	_order = actors.keys()
	_flair_ids = _order.filter(func(i: Variant) -> bool: return str(actors[i]["flair"]) != "")


## The baked sheet's inputs for one person: the facing (from where they walk or look, relative to the eye), the shader's row, depth fog and brightness, and the light
## they stand in. Presentation only: a pure function of the person's state and the camera.
func _sheet_look(a: Dictionary, c: StoryCharacter, st: String, walking: bool, alpha: float, lit: float) -> void:
	var fdir := Vector2.ZERO
	var pos: Vector2 = a["pos"]
	if bool(a.get("look_has", false)) and not walking:  # a directed act with a `look_at`: turned towards it (the camera: facing us)
		fdir = (a["look_pt"] as Vector2) - pos
	elif walking or st == "pace" or st == "serve":
		fdir = a.get("heading", Vector2.ZERO)
		if not walking:
			var pc: Dictionary = _pace_of(a)
			fdir = (pc["axis"] as Vector2) * signf(cos(_t_now * bpm / 60.0 * PI / 16.0 + float(a["seed"])) + 1.0e-6)
	elif st in StoryCharacter.PAIRED and str(a["partner"]) != "" and actors.has(str(a["partner"])):
		fdir = (actors[str(a["partner"])]["pos"] as Vector2) - pos
	elif st in StoryCharacter.TARGETED or st in ["check", "paint"] and str(a["data"].get("target", "")) != "":
		fdir = _target_of(a) - pos
	elif st == "mix":
		fdir = (circle_c if circle_c != Vector2.ZERO else riser_spot) - pos
	c.facing = 0
	c.face_flip = false
	if fdir.length() > 0.05:
		var to_eye := (Vector2(_eye.x, _eye.z) - pos).normalized()
		var d := fdir.normalized()
		var f := d.dot(to_eye)
		if f < -0.55:
			c.facing = 2
		elif f < 0.45:
			c.facing = 1
			c.face_flip = d.dot(_rgt) < 0.0
	var depth := float(a.get("depth", 0.0))
	var fog := clampf((depth - fog_m.x) / (fog_m.y - fog_m.x), 0.0, 1.0)
	var row := int(c.sheet.get("row", 0))
	c.self_modulate = Color((float(row) + 0.5) / 256.0, fog, 0.5 * lit, 1.0)
	c.modulate = Color(1, 1, 1, alpha)
	if light_fn.is_valid():
		var cell := Vector2i(int(pos.x * 2.0), int(pos.y * 2.0))  # the lamps' light is static: looked up again only when the person moves half a metre
		if a.get("light_cell", Vector2i(-99999, -99999)) != cell:
			a["light_cell"] = cell
			a["lamp"] = light_fn.call(str(a.get("sec", "")), pos, false)
		people.set_light(row, (light_fn.call(str(a.get("sec", "")), pos, true) as Color) * (a["lamp"] as Color))


## Put the crowd in the 3D world: homes, the door, the circle and the riser come from the map (metres), the rear silhouettes and occluders become props.
func attach_map(p_map: StoryMap) -> void:
	map = p_map
	world_mode = true
	_room_sectors = []
	for sec in map.sectors:
		if str(sec["room"]) == view:
			_room_sectors.append(str(sec["id"]))
	for id in actors:  # people of this crowd may stand in other rooms (a bar, a balcony, a sofa alcove): those sectors count as this crowd's too
		var hh: Dictionary = map.home(str(id))
		if not hh.is_empty() and str(hh["sector"]) not in _room_sectors:
			_room_sectors.append(str(hh["sector"]))
	var door := map.room_spot(view, "door")
	door_pos = door.get("at", Vector2.ZERO)
	door_slots = door.get("slots", [])
	var circ := map.room_spot(view, "circle")
	circle_c = circ.get("at", Vector2.ZERO)
	circle_r = circ.get("radii", Vector2(3.0, 1.8))
	circle_open = circ.get("open", Vector2(0, -1))
	riser_spot = map.room_spot(view, "riser").get("at", Vector2.ZERO)
	var lo := INF
	var hi := -INF
	for sec in map.sectors:
		if "dance_floor" in (sec["flags"] as Array) and str(sec["room"]) == view:
			for q in (sec["poly"] as PackedVector2Array):
				lo = minf(lo, q.x)
				hi = maxf(hi, q.x)
	if lo < hi:
		floor_x = Vector2(lo, hi)
	for id in actors:
		var a: Dictionary = actors[id]
		var h: Dictionary = map.home(str(id))
		if h.is_empty():
			continue
		a["home"] = h["at"]
		a["pos"] = h["at"]
		a["sec"] = str(h["sector"])
		a["k"] = HERO_M / maxf(float((a["node"] as StoryCharacter).rig.get("height", 260.0)), 1.0)
	for pr in props:
		remove_child(pr)
		pr.queue_free()
	props = []
	_sils = _sils.filter(func(x: Dictionary) -> bool: return not x.has("node"))
	for s in data.silhouettes:
		if str(s.get("view", "main")) != view:
			continue
		var sp: Dictionary = map.silhouettes.get(str(s["id"]), {})
		var shape: Dictionary = assets.manifest.get("silhouettes", {}).get(str(s["shape"]), {})
		if sp.is_empty() or shape.is_empty():
			continue
		var pn := StoryCrowdProp.new()
		pn.kind = "silhouette"
		pn.name = "Sil_" + str(s["id"])
		add_child(pn)
		props.append(pn)
		_sils.append({"idle": assets._entry(shape.get("idle", {})), "up": assets._entry(shape.get("up", {})), "at": sp["at"], "sector": str(sp["sector"]), "group": str(s["group"]),
			"thresh": float(s["thresh"]), "present": str(s["group"]) == "core", "alpha": 1.0 if str(s["group"]) == "core" else 0.0, "ph": _rng.randf(), "node": pn})
	for o in map.occluders:
		if map.room_of(str(o["sector"])) != view:
			continue
		var tex: Texture2D = assets.texture("textures/%s.png" % str(o["sprite"])) if assets != null and not str(map.textures.get(str(o["sprite"]), "")).begins_with("res://") else null
		if tex == null and assets != null:
			var file := str(map.textures.get(str(o["sprite"]), ""))
			tex = assets.texture(file)
		var pn2 := StoryCrowdProp.new()
		pn2.kind = "occluder"
		pn2.name = "Occ_" + str(o["id"])
		pn2.set_meta("def", o)
		pn2.set_meta("tex", tex)
		add_child(pn2)
		props.append(pn2)
	reset()


static func _id_seed(id: String) -> int:  # a stable small number per actor id (not String.hash: that may change between engine versions)
	var h := 7
	for i in id.length():
		h = (h * 31 + id.unicode_at(i)) % 100003
	return h


## Break-dance flair (docs/DANCE_POLISH.md): about one dancer in eleven carries one move (StoryCharacter.FLAIR_MOVES), by the same hash the sheet baker uses
## (tools/story/art/people_sheets.flair_of), so exactly those people have the move's frames.
static func flair_of(id: String) -> String:
	var sd := _id_seed(id)
	if (sd * 31 + 7) % 10007 % 11 != 0:
		return ""
	return StoryCharacter.FLAIR_MOVES[(sd * 70 + 3) % 997 % 4]


const FLAIR_CAP := 3  # never more than this many flair bursts at once in one room
const FLAIR_E := 50.0  # the dancer's own energy (room energy + threshold) a burst needs: a dancing room, not a quiet one
var _flair_ids: Array = []
var _flair_now: Dictionary = {}  # id -> move: the bursts scheduled for the current bar (after the cap)


## Whether a flair dancer's burst covers bar `bar`: in every four-bar phrase a dancer takes one slot (a move of FLAIR_BARS bars that starts on a bar of the
## phrase, a multiple of its length, and ends inside it) on six phrases in ten. A pure function of the person and the bar, so the bursts are the same on every run and land on the bar.
static func flair_scheduled(sd: int, move: String, bar: int) -> bool:
	if bar < 2:
		return false
	var phrase := bar / 4
	var bars := int(StoryCharacter.FLAIR_BARS.get(move, 1))
	if (sd * 13 + phrase * 7919) % 101 >= 60:
		return false
	var slot := ((sd + phrase * 3) % (4 / bars)) * bars  # a two-bar move starts on bar 1 or 3 of the phrase, so its cycle lines up with the burst
	var k := bar % 4 - slot
	return k >= 0 and k < bars


## The bursts of the bar at song position `beats`: the scheduled flair dancers who are in the room, in actor order, at most FLAIR_CAP of them.
func flair_bursts(beats: float) -> Dictionary:
	var bar := int(floorf(beats / 4.0))
	var out := {}
	for id in _flair_ids:
		var a: Dictionary = actors[id]
		if not a["present"] or not flair_scheduled(int(a["seed"]), str(a["flair"]), bar):
			continue
		out[id] = str(a["flair"])
		if out.size() >= FLAIR_CAP:
			break
	return out


func _xv(a: Dictionary) -> int:  # a stable per-dancer number for the little variations in the mood
	return int(640.0 + (a["home"] as Vector2).x * 65.0)


func reset() -> void:
	for id in actors:
		var a: Dictionary = actors[id]
		a["present"] = str(a["data"]["group"]) == "core"
		a["alpha"] = 1.0 if a["present"] else 0.0
		a["pos"] = a["home"]
		a["move"] = {}
		a["dir"] = {}
		a["stay"] = false
		a["vanish"] = {}
		(a["node"] as StoryCharacter).sync = false
	for s in _sils:
		s["present"] = s["group"] == "core"
		s["alpha"] = 1.0 if s["present"] else 0.0
	glow_on = false
	_last_t = -INF
	_ending = ""
	_flinch_until = -1.0
	_order_key = ""


func present_count() -> int:
	var n := 0
	for id in actors:
		if actors[id]["present"] and float(actors[id]["alpha"]) > 0.05:
			n += 1
	for s in _sils:
		if s["present"] and float(s["alpha"]) > 0.05:
			n += 1
	return n


func state_counts() -> Dictionary:
	var out := {}
	for id in actors:
		var a: Dictionary = actors[id]
		if a["present"]:
			var st: String = (a["node"] as StoryCharacter).state
			out[st] = int(out.get(st, 0)) + 1
	return out


# --- per frame -------------------------------------------------------------------------------------------------------

func update(t: float, p_energy: float) -> void:
	energy = p_energy
	var e01 := clampf(energy / 100.0, 0.0, 1.0)
	drawn = 0
	cap_max = 0.0
	cap_over = 0
	cap_held = 0
	cap_gone = 0
	if map == null:
		return  # a crowd stands in a world: attach_map first
	if t < _last_t:  # a restart: fades start over
		_last_t = t
	var dt := clampf(t - _last_t, 0.0, 0.25) if _last_t > -INF else 0.0
	_last_t = t
	var fade := dt * (FADE_PER_S * (0.8 if reduced else 1.0))
	if _pairs_dirty:
		_rebuild_pairs()
	_flair_now = flair_bursts(t * bpm / 60.0) if not _flair_ids.is_empty() else {}
	for id in _order:
		var a: Dictionary = actors[id]
		var c: StoryCharacter = a["node"]
		var mv: Dictionary = a["move"]
		var walking := false
		c.walk_dir = 0.0
		if not mv.is_empty():
			var u := clampf((t - float(mv["t0"])) / maxf(float(mv["t1"]) - float(mv["t0"]), 0.001), 0.0, 1.0)
			if t >= float(mv["t0"]):
				var ue := u * u * (3.0 - 2.0 * u)
				var along := _along(mv, ue)
				a["pos"] = along[0]
				a["heading"] = along[1]
				var dx := _screen_dx(along[1])
				walking = u < 1.0
				c.walk_dir = clampf(dx, -1.0, 1.0) * sin(PI * clampf(u * 1.4, 0.0, 1.0)) if walking else 0.0
				if u >= 1.0:
					a["move"] = {}
					if mv.get("hide_after", false):
						a["present"] = false
					if mv.has("then"):
						a["dir"] = mv["then"]
		var vis_target := 1.0 if a["present"] else 0.0
		a["alpha"] = move_toward(float(a["alpha"]), vis_target, fade)  # song-time fade: the same at any frame rate
		c.visible = float(a["alpha"]) > 0.01
		if not c.visible:
			continue
		if not _room_visible:
			c.visible = false
			continue
		var vn: Dictionary = a["vanish"]
		var vu := 0.0
		if not vn.is_empty() and t >= float(vn["t0"]):
			vu = clampf((t - float(vn["t0"])) / maxf(float(vn["t1"]) - float(vn["t0"]), 0.001), 0.0, 1.0)
		var lit := 1.13 if id == lit_id else 1.0  # the followspot's dancer stands out from the crowd
		if _story_lit(a, t):
			lit = maxf(lit, STORY_LIT)  # a person acting for a hotspot or its outcome carries a light of their own (visual polish: they read in a dark room and in a crowd)
		var alpha := float(a["alpha"]) * (1.0 - clampf((vu - 0.55) / 0.45, 0.0, 1.0))
		var shown := _place_world(a, c, vu, id == lit_id or str(a["data"].get("role", "")) == "hero" or _held_by_story(a, t))  # false: behind a wall, out of view or inside the cap: not drawn and not posed, but it keeps its state
		if shown:
			alpha *= float(a["near"])
			drawn += 1
			var mag := float(a.get("mag", 0.0)) * (1.0 - 0.5 * vu)
			cap_max = maxf(cap_max, mag)
			if mag > FIG_CAP + 1.0e-3:
				cap_over += 1
		c.visible = shown
		c.modulate = Color(lit, lit, lit * 0.97, alpha)
		c.reduced = reduced
		c.glow_on = glow_on and c.glow
		var dir: Dictionary = a["dir"]
		while not dir.is_empty() and t >= float(dir["until"]):  # a directed act that ended hands over to the next of its chain, else the person's own life
			dir = _next_dir(dir)
			a["dir"] = dir
		var st := _mood_state(a, e01)
		st = _activity_extras(a, c, st, t)
		c.sync = false
		c.face_override = ""
		a["look_has"] = false
		if walking:
			st = "walk"
			c.toward = 0.0
		elif (str(a["lock"]) == "" or bool(dir.get("force", false))) and not dir.is_empty() and t < float(dir["until"]) and t >= float(dir.get("from", -1.0)):
			st = str(dir["state"])
			c.sync = bool(dir.get("sync", false))
			c.face_override = str(dir.get("face", ""))
			var lk := str(dir.get("look_at", ""))
			if lk != "":
				var lpt: Variant = look_point(lk)
				if lpt != null:
					a["look_has"] = true
					a["look_pt"] = lpt
					c.toward = _toward((lpt as Vector2) - (a["pos"] as Vector2))
		if not walking and (st == "dance" or st == "cheer") and not c.sync and _ending == "" and _flair_now.has(id) \
				and energy + float(a["thresh"]) >= FLAIR_E and _dancing_here(a):
			st = str(_flair_now[id])  # a burst of the dancer's flair move, then back to their dance
		if st != c.state:
			c.state = st
		if not shown:
			continue
		if c.people != null:
			_sheet_look(a, c, st, walking, alpha, lit)
		# the dancers animate at up to POSE_RATE a second of song time (the redraw is the cost); position and scale still follow the camera every frame
		var pt := float(a.get("pose_t", -1.0e9))
		if t >= pt and t - pt < 1.0 / (POSE_RATE if float(a["depth"]) < FAR_M else POSE_RATE_FAR):
			continue
		a["pose_t"] = t
		c.update_pose(t, bpm, e01)
	for s in _sils:
		s["alpha"] = move_toward(float(s["alpha"]), 1.0 if s["present"] else 0.0, fade)
		var up_target := 1.0 if energy + float(s["thresh"]) > SIL_UP_E or _ending == "legendary" else 0.0
		s["upw"] = move_toward(float(s.get("upw", up_target)), up_target, dt * 3.0)
	if _room_visible:
		_update_props()
		_sort_world()
	else:
		sort_items = []
		_drawn_ids = []
	queue_redraw()


# --- the 2.5D world: walking routes, projection, props, sorting --------------------------------------------------------------------------

## Where a walker is along its route (eased fraction u of the route length) and the direction it is heading.
func _along(mv: Dictionary, u: float) -> Array:
	var pts: PackedVector2Array = mv["path"]
	var cum: PackedFloat32Array = mv["cum"]
	var total := float(cum[cum.size() - 1])
	if total < 1.0e-6 or pts.size() < 2:
		return [pts[pts.size() - 1], Vector2.ZERO]
	var d := u * total
	var i := 1
	while i < pts.size() - 1 and d > float(cum[i]):
		i += 1
	var seg := float(cum[i]) - float(cum[i - 1])
	var k := clampf((d - float(cum[i - 1])) / maxf(seg, 1.0e-6), 0.0, 1.0)
	return [pts[i - 1].lerp(pts[i], k), (pts[i] - pts[i - 1]).normalized()]


## A ground heading as a sideways screen speed (-1 left .. 1 right) from the current camera, for the walk cycle's lean.
func _screen_dx(heading: Vector2) -> float:
	if cam_pose.is_empty():
		return heading.x
	return heading.dot(StoryProjector.right(float(cam_pose["yaw"])))


## Whether sector `sid` counts as this crowd's: while one of its sectors can be seen the crowd projects its people and its props.
func owns_sector(sid: String) -> bool:
	return _room_sectors.has(sid)


## Sector `sid` counts as this crowd's from now on: a prop standing there (a herald, a quest's gate) is projected whenever that sector can be seen, even when no sector of the
## crowd's own room can (a room of the map with no crowd of its own, the treatment room of the ward, borrows the main crowd).
func own_sector(sid: String) -> void:
	if sid != "" and not _room_sectors.has(sid):
		_room_sectors.append(sid)


func set_camera(pose: Dictionary, size: Vector2, visible_secs: Dictionary) -> void:
	cam_pose = pose
	view_size = size
	vis_sectors = visible_secs
	_room_visible = visible_secs.is_empty() or _room_sectors.is_empty()
	for sid in _room_sectors:
		if visible_secs.has(sid):
			_room_visible = true
			break
	var cam: Vector3 = pose["cam"]
	_eye = cam
	_fwd = StoryProjector.forward(float(pose["yaw"]))
	_rgt = StoryProjector.right(float(pose["yaw"]))
	_focal = StoryProjector.focal_px(size.y)
	_pitch = deg_to_rad(float(pose.get("pitch", 0.0)))
	_sin_p = sin(_pitch)
	_cos_p = cos(_pitch)


var _eye := Vector3.ZERO  # the camera, unpacked once a frame for the per-dancer projection
var _fwd := Vector2.ZERO
var _rgt := Vector2.ZERO
var _focal := 1.0
var _pitch := 0.0  # the head pitched up by this many radians (a look at the lights): the projection tilts with it
var _sin_p := 0.0
var _cos_p := 1.0


func _ground_of(sec: String) -> float:
	return float(map.sector(sec).get("floor", 0.0)) if sec != "" else 0.0


## Project one dancer: set its node's position and scale, `near` (the dissolve towards the size cap), `mag` (internal pixels per sheet pixel) and `depth`. False when it
## should not be drawn. `hold`: a person the story needs is held back at the cap distance instead of dissolving (FIG_CAP).
func _place_world(a: Dictionary, c: StoryCharacter, vu: float, hold := false) -> bool:
	if cam_pose.is_empty():
		return false
	var pos: Vector2 = a["pos"]
	var sec: String = str(a.get("sec", ""))
	if not a["move"].is_empty():  # a walker may have crossed into another sector
		var now := map.sector_at(pos)
		if now != "":
			sec = now
			a["sec"] = now
	if not vis_sectors.is_empty() and not vis_sectors.has(sec):
		return false
	var rel := pos - Vector2(_eye.x, _eye.z)  # the pinhole projection of StoryProjector.project_ground, inlined: it runs for every dancer every frame
	var along := rel.dot(_fwd)
	var up := _ground_of(sec) - _eye.y  # the feet are below the eye
	var depth := along * _cos_p + up * _sin_p if _pitch != 0.0 else along
	a["depth"] = depth
	if depth < StoryProjector.NEAR:
		return false
	var ppm := _focal / depth  # pixels per metre at this distance
	var ppm_cap := FIG_CAP * fig_m  # the most pixels per metre a person may get
	if ppm > ppm_cap and hold:  # held back: the same bearing, the feet on the floor at the cap distance
		var d_cap := _focal / ppm_cap
		var along2 := (d_cap - up * _sin_p) / _cos_p if _pitch != 0.0 else d_cap
		rel *= along2 / maxf(along, 1.0e-3)
		along = along2
		depth = d_cap
		a["depth"] = depth
		ppm = ppm_cap
		cap_held += 1
	var cy := up * _cos_p - along * _sin_p if _pitch != 0.0 else up
	var feet := Vector2(view_size.x * 0.5 + ppm * rel.dot(_rgt), view_size.y * 0.5 - ppm * cy)
	var tall := HERO_M * ppm  # the dancer's height on screen: close ones have their feet below the edge but their body in view
	if feet.x < -view_size.x * 0.25 or feet.x > view_size.x * 1.25 or feet.y - tall > view_size.y or feet.y < -view_size.y * 0.25:
		return false
	var mag := ppm / fig_m
	a["mag"] = mag
	a["near"] = clampf((FIG_CAP - mag) / (FIG_CAP - FIG_FADE), 0.0, 1.0) if not hold else 1.0
	if float(a["near"]) <= 0.0:
		cap_gone += 1
		return false
	var pr := {"scale": ppm, "screen": feet}
	var sc: float = ppm * float(a["k"]) * (1.0 - 0.5 * vu)
	var vn: Dictionary = a["vanish"]
	var dy := float(vn.get("dy", 0.0)) * vu * vu * float(a["k"]) * float(pr["scale"])
	c.position = (pr["screen"] as Vector2) + Vector2(sin(vu * 9.0 + float(a["thresh"])) * 6.0 * vu * sc, dy)
	c.scale = Vector2(sc, sc)
	return true


func _update_props() -> void:
	if cam_pose.is_empty():
		return
	var beats := _t_now * bpm / 60.0
	var rise := sin(PI * fposmod(beats, 1.0))
	var tint := Color(0.55, 0.6, 0.85).lerp(Color(0.78, 0.76, 1.0), clampf((energy - 20.0) / 30.0, 0.0, 1.0))
	for pn in props:
		var p: StoryCrowdProp = pn
		p.items = []
		p.depth = 1.0e9
		if p.kind == "occluder":
			var o: Dictionary = p.get_meta("def")
			var tex: Texture2D = p.get_meta("tex")
			var sec := str(o["sector"])
			var at: Vector2 = o["at"]
			if tex == null or (not vis_sectors.is_empty() and not vis_sectors.has(sec)):
				p.visible = false
				continue
			var pr := StoryProjector.project_ground(at.x, at.y, _ground_of(sec), cam_pose, view_size)
			p.visible = bool(pr["visible"])
			if not p.visible:
				continue
			var w := float(o["width"]) * float(pr["scale"])
			var h := float(o["height"]) * float(pr["scale"])
			var col: Color = tint_fn.call(sec) if tint_fn.is_valid() else Color.WHITE
			p.position = pr["screen"]
			p.depth = float(pr["depth"])
			p.items = [[tex, Rect2(-w * 0.5, -h, w, h), col]]
			p.queue_redraw()
		else:
			pass
	for s in _sils:
		if not s.has("node"):
			continue
		var p2: StoryCrowdProp = s["node"]
		var al := float(s["alpha"])
		p2.items = []
		p2.depth = 1.0e9
		var sec2 := str(s["sector"])
		if al < 0.02 or (not vis_sectors.is_empty() and not vis_sectors.has(sec2)):
			p2.visible = false
			continue
		var at2: Vector2 = s["at"]
		var pr2 := StoryProjector.project_ground(at2.x, at2.y, _ground_of(sec2), cam_pose, view_size)
		p2.visible = bool(pr2["visible"]) and float(pr2["depth"]) >= SIL_NEAR_M  # a rear-row silhouette never stands nearer than SIL_NEAR_M (style guide section 9)
		if not p2.visible:
			continue
		var sway := sin((beats * 0.25 + float(s["ph"])) * TAU) * (2.0 + energy * 0.05)
		var bob := rise * (1.0 + energy * 0.07) * clampf((energy - 25.0) / 15.0, 0.0, 1.0)
		var upw := float(s.get("upw", 0.0))
		var k := float(pr2["scale"]) * HERO_M / 260.0
		p2.position = (pr2["screen"] as Vector2) + Vector2(sway * k, -bob * k)
		p2.depth = float(pr2["depth"])
		for j in 2:
			var ent: Dictionary = s["up"] if j == 1 else s["idle"]
			var wgt := upw if j == 1 else 1.0 - upw
			if wgt < 0.01 or ent.is_empty() or ent["tex"] == null:
				continue
			var kk: float = k * float(ent["scale"])
			var tx: Texture2D = ent["tex"]
			p2.items.append([tx, Rect2(-(ent["pivot"] as Vector2) * kk, Vector2(tx.get_width(), tx.get_height()) * kk), Color(tint, al * wgt)])
		p2.queue_redraw()


## Painter's order, far to near: the visible dancers, silhouettes and occluders of this crowd with their depth keys (millimetres from the eye, inverted so far sorts first).
## The stage merges every crowd's items and gives each node a z_index by that one order, so a dancer in the next room stands behind or in front of this room's by true
## distance, whichever crowd it belongs to (a doorway no longer mis-orders them).
var sort_items: Array = []  # [[key: int, node: CanvasItem], ...] sorted far to near, visible nodes only
var _drawn_ids: Array = []


func _sort_world() -> void:
	sort_items = []
	var keyed: Array = []
	var nodes: Array = []
	for id in _order:
		var c: StoryCharacter = actors[id]["node"]
		if c.visible:
			nodes.append(c)
			keyed.append((4000000 - int(clampf(float(actors[id].get("depth", 0.0)), 0.0, 3999.0) * 1000.0)) << 10 | (nodes.size() - 1))
	for pn in props:
		if pn.visible:
			nodes.append(pn)
			keyed.append((4000000 - int(clampf((pn as StoryCrowdProp).depth, 0.0, 3999.0) * 1000.0)) << 10 | (nodes.size() - 1))
	keyed.sort()
	_drawn_ids = []
	for k in keyed:
		var n: Node = nodes[int(k) & 1023]
		sort_items.append([int(k) >> 10, n])
		if n is StoryCharacter:
			_drawn_ids.append((n as StoryCharacter).actor_id)


## The ids of the dancers drawn this frame, far to near (what the tests check).
func drawn_order() -> Array:
	return _drawn_ids


## Dancing happens on dance floors, stages, steps and booths; everywhere else people do what the sector's `activities` say for the band.
static func dancing_flags(flags: Array) -> bool:
	return "dance_floor" in flags or "stage" in flags or "stage_steps" in flags or "booth" in flags


func _dancing_here(a: Dictionary) -> bool:
	return map == null or dancing_flags(map.sector(str(a.get("sec", ""))).get("flags", []))


## The activity a person picks in their sector at an energy band: by their own seed from the sector's list (never random per frame), or the fixed `activity` of a character with a
## part to play (a DJ at the decks, a bouncer at the door).
func pick_activity(a: Dictionary, band: String) -> String:
	if str(a["lock"]) != "":
		return str(a["lock"])
	var key := str(a.get("sec", "")) + "|" + band  # a pure function of the person, their sector and the band: looked up once
	var memo: Dictionary = a.get("pick_memo", {})
	if memo.has(key):
		return memo[key]
	var list: Array = map.activities_of(str(a.get("sec", "")), band) if map != null else ["dance"]
	var out := str(list[(int(a["seed"]) + 3 * maxi(StoryData.band_rank(band), 0)) % list.size()])
	memo[key] = out
	a["pick_memo"] = memo
	return out


func _mood_state(a: Dictionary, e01: float) -> String:
	var ee := energy + float(a["thresh"])
	var here := _dancing_here(a)
	if _ending != "" and here and str(a["lock"]) == "":
		return _ending_state(a, ee)
	var act := pick_activity(a, data.band_of(ee))
	if act == "dance":
		if ee < 32.0:
			return "idle"
		if ee < 70.0:
			return "dance"
		if ee < 88.0:
			return "dance" if (_xv(a) / 40) % 3 != 0 else "cheer"
		return "cheer"
	if act == "stand":
		return "sad" if ee < 18.0 else "idle"
	return act


func _ending_state(a: Dictionary, ee: float) -> String:
	match _ending:
		"legendary":
			return "cheer" if _xv(a) % 3 != 0 else "hands_up"
		"good":
			return "clap" if _xv(a) % 2 == 0 else "dance"
		_:
			return "sad" if _xv(a) % 3 != 0 else ("clap" if _xv(a) % 6 == 0 else "look")


func _draw() -> void:
	_draw_blobs()


## Flat contact shadows in the world: one dark ellipse under each drawn dancer (smaller in the air), drawn first so every dancer and prop covers them.
func _draw_blobs() -> void:
	for id in _order:
		var a: Dictionary = actors[id]
		var c: StoryCharacter = a["node"]
		if not c.visible or c.modulate.a < 0.05:
			continue
		var air := clampf(float(c.cur.get("jump", 0.0)) / 30.0, 0.0, 1.0)
		var ppm: float = c.scale.x * float(c.rig.get("height", 260.0)) / HERO_M  # pixels per metre at this dancer
		var r := 0.42 * ppm * (1.0 - 0.35 * air)
		draw_set_transform(c.position + Vector2(float(c.cur.get("sway_x", 0.0)) * c.scale.x, 0.0), 0.0, Vector2(1.0, 0.3))
		draw_circle(Vector2.ZERO, maxf(r, 1.0), Color(0.0, 0.0, 0.04, 0.5 * c.modulate.a * (1.0 - 0.5 * air)))
	draw_set_transform_matrix(Transform2D.IDENTITY)


var _t_now := 0.0
var _last_t := -INF
const FADE_PER_S := 3.0  # arrivals and exits fade over a third of a second of song time


func set_time(t: float) -> void:
	_t_now = t


## Pairs, targets, props and pacing for the activity the person is in. Returns the state to show (an activity that needs a partner falls back when it has none).
const DEFAULT_PROPS := {"drink": "cup", "toast": "cup", "phone": "phone", "paint": "brush", "carry": "tray", "serve": "tray", "check": "clipboard"}


func _activity_extras(a: Dictionary, c: StoryCharacter, st: String, t: float) -> String:
	if st != str(a["act"]):
		a["act"] = st
		_pairs_dirty = true
	var pos: Vector2 = a["pos"]
	c.toward = 0.0
	if st in StoryCharacter.PAIRED:
		var pid := str(a["partner"])
		if pid == "" or not actors.has(pid):
			st = "drink" if st == "toast" else "stand"
		else:
			c.toward = _toward((actors[pid]["pos"] as Vector2) - pos)
			c.chat_role = 0 if str(a["node"].actor_id) < pid else 1
	elif st in StoryCharacter.TARGETED:
		c.toward = _toward(_target_of(a) - pos)
	elif st == "lie" or st == "lean_wall":
		c.toward = 1.0 if int(a["seed"]) % 2 == 0 else -1.0
	var fixed := str(a["data"].get("prop", ""))
	c.held = fixed if fixed != "" else str(DEFAULT_PROPS.get(st, ""))
	if c.held == "cup" and int(a["seed"]) % 3 == 0:
		c.held = "bottle"
	if st == "pace" or st == "serve":  # walk to and fro along an axis in the person's sector, never leaving it
		if a["move"].is_empty():
			var pc: Dictionary = _pace_of(a)
			var ph := sin(t * bpm / 60.0 * PI / 16.0 + float(a["seed"]))
			a["pos"] = (a["home"] as Vector2) + (pc["axis"] as Vector2) * float(pc["amp"]) * ph
			a["pace_on"] = true
			c.walk_dir = clampf(cos(t * bpm / 60.0 * PI / 16.0 + float(a["seed"])) * (pc["axis"] as Vector2).dot(_rgt), -1.0, 1.0)
	elif bool(a.get("pace_on", false)):
		a["pace_on"] = false
		if a["move"].is_empty():
			a["pos"] = a["home"]
	return st


func _toward(d: Vector2) -> float:
	var dx := d.dot(_rgt)
	if absf(dx) < 0.15:
		return 0.3 if dx >= 0.0 else -0.3
	return clampf(dx * 0.8, -1.0, 1.0)


## Where a watcher or starer looks: their `target` (a waypoint or a person's home), else the stage of their room, else the middle of the room.
func _target_of(a: Dictionary) -> Vector2:
	if bool(a.get("look_has", false)):  # a directed act's `look_at` beats the person's own target
		return a["look_pt"]
	var tid := str(a["data"].get("target", ""))
	if tid != "" and map != null:
		if map.has_waypoint(tid):
			return map.waypoint(tid)["at"]
		var h := map.home(tid)
		if not h.is_empty():
			return h["at"]
	return riser_spot if riser_spot != Vector2.ZERO else circle_c


func _pace_of(a: Dictionary) -> Dictionary:
	if a.has("pace"):
		return a["pace"]
	var axis := Vector2.RIGHT
	var raw_axis: Variant = a["data"].get("pace_axis", null)
	if typeof(raw_axis) == TYPE_ARRAY and (raw_axis as Array).size() == 2:
		axis = Vector2(float(raw_axis[0]), float(raw_axis[1])).normalized()
	var amp := float(a["data"].get("pace_m", 1.4))
	var sec := str(a.get("sec", ""))
	while amp > 0.0 and not (map.inside((a["home"] as Vector2) + axis * amp, sec, 0.3) and map.inside((a["home"] as Vector2) - axis * amp, sec, 0.3)):
		amp -= 0.1
	a["pace"] = {"axis": axis, "amp": maxf(amp, 0.0)}
	return a["pace"]


var _pairs_dirty := true


## Pair the people who are in a paired activity (chat, hug, toast) in the same sector: the nearest free person of the same activity, in actor order.
func _rebuild_pairs() -> void:
	_pairs_dirty = false
	for id in _order:
		actors[id]["partner"] = ""
	for act in StoryCharacter.PAIRED:
		var pool: Array = []
		for id in _order:
			var a: Dictionary = actors[id]
			if str(a["act"]) == act and a["present"]:
				pool.append(id)
		for id in pool:
			var a: Dictionary = actors[id]
			if str(a["partner"]) != "":
				continue
			var best := ""
			var bd := 5.0
			for other in pool:
				var o: Dictionary = actors[other]
				if other == id or str(o["partner"]) != "" or str(o.get("sec", "")) != str(a.get("sec", "")):
					continue
				var dd := (o["home"] as Vector2).distance_to(a["home"])
				if dd < bd:
					bd = dd
					best = other
			if best != "":
				a["partner"] = best
				actors[best]["partner"] = id


# --- actions ---------------------------------------------------------------------------------------------------------

func ids_of(group: String) -> Array:
	if data.groups.has(group):
		return data.groups[group].filter(func(i: Variant) -> bool: return actors.has(str(i)))
	var out: Array = []
	for id in actors:
		if str(actors[id]["data"]["group"]) == group:
			out.append(id)
	return out


func present_ids() -> Array:
	var out: Array = []
	for id in _order:
		if actors[id]["present"]:
			out.append(id)
	return out


func direct(ids: Array, state: String, t0: float, seconds: float, sync := false, stagger := 0.0) -> void:
	var k := 0
	for id in ids:
		if not actors.has(id):
			continue
		var a: Dictionary = actors[id]
		if not a["present"] or str(a["lock"]) != "" or not _dancing_here(a) or _acted(a, t0):  # a directive moves the dancing crowd, not the people at the bar or a bouncer at his door
			continue
		a["dir"] = {"state": state, "from": t0 + float(k) * stagger, "until": t0 + seconds + float(k) * stagger, "sync": sync}
		k += 1


## The per-activity states (CONTRACTS.md 10, package A8): each is a row of the figure sheets when the sheet was baked with it; a sheet without it falls back to the first
## of these candidates that the person's sheet (or the live rig) has, [state, face]. The plain crowd states play as they are where the sheet has them (CROWD_FALLBACKS otherwise).
const ACTIVITY_STATES := {
	"waiting": [["waiting", ""], ["queue", ""], ["stand", ""], ["idle", ""]],
	"happy": [["happy", ""], ["nod", "happy"], ["clap", ""], ["cheer", ""], ["idle", "happy"]],
	"impatient": [["impatient", ""], ["shake_head", "anger"], ["stamp", "anger"], ["look", ""], ["idle", "anger"]],
	"frown": [["frown", ""], ["shake_head", "doubt"], ["sad", ""], ["idle", "sad"]],
	"beckon": [["beckon", ""], ["wave", ""], ["point", ""], ["idle", ""]],
	"deal": [["deal", ""], ["offer", ""], ["point", ""], ["idle", ""]],  # (the card table's dealer, package A8b: dealing, paying, sweeping the stake)
	"raise_glass": [["raise_glass", ""], ["toast", ""], ["drink", ""], ["cheer", ""], ["idle", ""]],
}
## The crowd states an activity also asks for, with fallbacks for a sheet baked without them (a directed actor's sheet has its acts, not always the crowd's moves).
const CROWD_FALLBACKS := {
	"clap": [["clap", ""], ["cheer", ""], ["nod", "happy"], ["idle", "happy"]],
	"hands_up": [["hands_up", ""], ["cheer", ""], ["wave", ""], ["idle", "happy"]],
	"cheer": [["cheer", ""], ["wave", ""], ["laugh", ""], ["idle", "happy"]],
	"look": [["look", ""], ["idle", ""]],
	"idle": [["idle", ""]],
}


## What actor `id` will show for activity state `state`: {state: the state played, face, fallback: true when it is not `state` itself, sheet_state: the sheet row it shows
## (StoryCharacter.sheet_pick; "" with the live rig)}. {} for an unknown actor.
func resolve_state(id: String, state: String) -> Dictionary:
	if not actors.has(id):
		return {}
	var c: StoryCharacter = actors[id]["node"]
	var has := func(st: String) -> bool:
		if c.uses_sheet():
			return (c.sheet.get("states", {}) as Dictionary).has(st)
		return st in StoryCharacter.STATES
	var cands: Array = ACTIVITY_STATES.get(state, CROWD_FALLBACKS.get(state, [[state, ""], ["idle", ""]]))
	var pick: Array = cands[cands.size() - 1]
	for cd: Array in cands:
		if has.call(str(cd[0])):
			pick = cd
			break
	var out := {"state": str(pick[0]), "face": str(pick[1]), "fallback": str(pick[0]) != state, "sheet_state": ""}
	if c.uses_sheet():
		var keep := [c.state, c.face_override]
		c.state = out["state"]
		c.face_override = out["face"]
		out["sheet_state"] = str(c.sheet_pick(0.0)[0])
		c.state = keep[0]
		c.face_override = keep[1]
	return out


## An activity directs one of its people (the customer, the attendant, the bartender): `state` (an ACTIVITY_STATES key or any crowd state) from song time `t0` for `dur`
## seconds (0: until the next call), resolved to what their sheet has (resolve_state). Forced (a bartender at his post plays it too); someone not yet in the room fades in.
## Returns the resolution ({} for an unknown actor).
func person(id: String, state: String, t0: float, dur: float = 0.0) -> Dictionary:
	var r := resolve_state(id, state)
	if r.is_empty():
		return r
	ensure_present(id)
	direct_chain(id, [{"act": str(r["state"]), "face": str(r["face"]), "look_at": "", "from": t0, "until": t0 + dur if dur > 0.0 else NO_END}], "activity")
	return r


## A person beckons the player (a hotspot anchored on an actor with no `acting` block): they wave at us until `until`, even a bartender or a bouncer with a fixed activity. `stand_down` puts them back.
func beckon(id: String, t0: float, until: float) -> void:
	direct_actor(id, "wave", "", t0, until, "", "hotspot")


## The acting contract (docs/THREE_PATHS_AND_FACES_PLAN.md 2.3): tells one named person to do `act` with `face`, from song time `t0` until `until`, looking at `look_at` ("camera", an actor id, a thing
## or a waypoint of the map; "" = as they are). Forced, so it moves a bartender or a bouncer too. `src` says who asked ("hotspot": the view's available/selected act, "outcome": a commit's chain,
## "cast": a scene's story beat) so `stand_down` and the hotspot view never wipe someone else's act. Returns false when the person is not in this room or not present.
## (The plan names this `direct`; that name is the crowd's group directive and keeps its signature, so the person-directing one is `direct_actor`.)
func direct_actor(id: String, act: String, face: String, t0: float, until: float, look_at := "", src := "") -> bool:
	return direct_chain(id, [{"act": act, "face": face, "look_at": look_at, "from": t0, "until": until}], src)


## The person a hotspot asks you to touch is in the room: someone who has not come in yet (a gatherer, an early or late arrival; the continuous run brings none of them in by itself) fades in at their own place.
## False when there is nobody of that name here.
func ensure_present(id: String) -> bool:
	if not actors.has(id):
		return false
	if not bool(actors[id]["present"]):
		actors[id]["present"] = true
	return true


## A person who is not in this scene (a cast line with `hide`: the companion lost on the road): gone from the crowd at once. A new run brings the people back (reset).
func hide_actor(id: String) -> bool:
	if not actors.has(id):
		return false
	actors[id]["present"] = false
	actors[id]["alpha"] = 0.0
	actors[id]["move"] = {}
	actors[id]["dir"] = {}
	(actors[id]["node"] as StoryCharacter).visible = false
	return true


## A chain of acts played end to end: [{act, face, look_at, from, until}, ...] (RunActing.outcome_chain). Each hands over to the next when it ends; the last hands back to the person's own life.
func direct_chain(id: String, segs: Array, src := "") -> bool:
	if segs.is_empty() or not actors.has(id) or not bool(actors[id]["present"]):
		return false
	actors[id]["dir"] = _dir_of(segs[0], src, segs.slice(1))
	return true


func _dir_of(seg: Dictionary, src: String, rest: Array) -> Dictionary:
	return {"state": str(seg["act"]), "from": float(seg["from"]), "until": float(seg["until"]), "sync": false, "force": true, "face": str(seg.get("face", "")), "look_at": str(seg.get("look_at", "")),
		"src": src, "chain": rest}


func _next_dir(dir: Dictionary) -> Dictionary:
	var rest: Array = dir.get("chain", [])
	return _dir_of(rest[0], str(dir.get("src", "")), rest.slice(1)) if not rest.is_empty() else {}


## Who is directing `id` at song time `t` (the `src` of the act in force: "hotspot", "outcome", "cast"), "" when nobody is.
func directing(id: String, t: float) -> String:
	if not actors.has(id):
		return ""
	var dir: Dictionary = actors[id]["dir"]
	if dir.is_empty() or not bool(dir.get("force", false)) or t >= float(dir["until"]) or t < float(dir.get("from", -1.0)):
		return ""
	return str(dir.get("src", ""))


## Where `target` is on the ground (metres, x and z) for a `look_at`: "camera" is the eye; else a person of this room, a person's home, a waypoint or a thing of the map. null when it cannot be placed.
func look_point(target: String) -> Variant:
	if target == "camera":
		return Vector2(_eye.x, _eye.z)
	if actors.has(target):
		return actors[target]["pos"]
	if map == null:
		return null
	var h: Dictionary = map.home(target)
	if not h.is_empty():
		return h["at"]
	if map.has_waypoint(target):
		return map.waypoint(target)["at"]
	for t in map.things:
		if str(t["id"]) == target:
			return t["at"]
	return null


## Whether the story needs a person whole at `t` (held back at the size cap, never dissolved): a forced act is running (a hotspot's, an outcome's, a cast line's; not a room-wide wave).
func _held_by_story(a: Dictionary, t: float) -> bool:
	var dir: Dictionary = a["dir"]
	return bool(dir.get("force", false)) and t < float(dir.get("until", -1.0)) and t >= float(dir.get("from", -1.0e9))


## Whether a person is acting for a hotspot (its available or selected act) or for a hotspot's outcome at `t`.
func _story_lit(a: Dictionary, t: float) -> bool:
	var dir: Dictionary = a["dir"]
	return bool(dir.get("force", false)) and str(dir.get("src", "")) in ["hotspot", "outcome"] and t < float(dir.get("until", -1.0)) and t >= float(dir.get("from", -1.0))


## Whether a person is acting for the story at `t` (a hotspot's act, an outcome or a cast line, all `force`d): the room's group moves (react, wave, direct) leave them alone, or a two-bar cheer
## would wipe a selected act for good (the hotspot view directs a state once).
func _acted(a: Dictionary, t: float) -> bool:
	var dir: Dictionary = a["dir"]
	return bool(dir.get("force", false)) and t < float(dir.get("until", -1.0))


## Puts a person back to their own life. With `only_src` it clears only an act that source asked for (the hotspot view stands its own down; a commit's outcome or a story beat keeps playing).
func stand_down(id: String, only_src := "") -> void:
	if not actors.has(id):
		return
	var dir: Dictionary = actors[id]["dir"]
	if not bool(dir.get("force", false)):
		return
	if only_src == "" or str(dir.get("src", "")) == only_src:
		actors[id]["dir"] = {}


## A wave of `state` travelling left to right across the room over `seconds`, each dancer holding it for `hold` seconds.
func wave(t0: float, seconds: float, hold: float, state := "cheer") -> void:
	for id in present_ids():
		var a: Dictionary = actors[id]
		if str(a["lock"]) != "" or not _dancing_here(a) or _acted(a, t0):
			continue
		var u := clampf((float((a["pos"] as Vector2).x) - floor_x.x) / maxf(floor_x.y - floor_x.x, 0.001), 0.0, 1.0)
		a["dir"] = {"state": state, "from": t0 + u * seconds, "until": t0 + u * seconds + hold, "sync": false}


func walk_to(id: String, to: Vector2, t0: float, seconds: float, then: Dictionary = {}, hide_after := false) -> void:
	if not actors.has(id):
		return
	var a: Dictionary = actors[id]
	a["move"] = {"from": a["pos"], "to": to, "t0": t0, "t1": t0 + seconds, "then": then, "hide_after": hide_after}
	var from: Vector2 = a["pos"]  # walk the sector graph (through the doors), never through a wall
	var from_sec := map.sector_at(from)
	var to_sec := map.sector_at(to)
	var pts := PackedVector2Array([from, to])
	if from_sec != "" and to_sec != "":
		var r := map.route(from, from_sec, to, to_sec)
		if (r["points"] as PackedVector2Array).size() >= 2:
			pts = r["points"]
	var cum := PackedFloat32Array([0.0])
	for i in range(1, pts.size()):
		cum.append(cum[i - 1] + pts[i - 1].distance_to(pts[i]))
	a["move"]["path"] = pts
	a["move"]["cum"] = cum


func bring_in(group: String, t0: float, seconds := 4.0, from_door := true) -> void:
	var k := 0
	for id in ids_of(group):
		var a: Dictionary = actors[id]
		if a["present"] and a["move"].is_empty():
			continue
		a["present"] = true
		var start: Vector2 = door_pos + Vector2(float(k % 3) * 0.3, 0.0)
		if str(a["data"].get("enter_from", "doorway")) == "side":
			start = _side_start(a)
		a["pos"] = start
		a["alpha"] = 0.0
		walk_to(id, a["home"], t0 + float(k) * 0.45, seconds)
		k += 1
	for s in _sils:
		if s["group"] == group:
			s["present"] = true


## Where someone coming in from the side starts: the left or right door of the room, by which side their place is on.
func _side_start(a: Dictionary) -> Vector2:
	return map.room_spot(view, "side_l" if (a["home"] as Vector2).x < (map.room_spot(view, "circle").get("at", Vector2.ZERO) as Vector2).x else "side_r").get("at", door_pos)


## Where a person waiting at the door stands (door_slot indexes the map's door slots).
func _door_wait(a: Dictionary, k: int) -> Vector2:
	var slot := int(a["data"].get("door_slot", k))
	if not door_slots.is_empty():
		return door_slots[slot % door_slots.size()]
	return door_pos + Vector2(float(slot % 4) * 0.5, 0.5 + float(slot / 4) * 0.5)


func gather_at_door(group: String, t0: float) -> void:
	var k := 0
	for id in ids_of(group):
		var a: Dictionary = actors[id]
		a["present"] = true
		var wait := _door_wait(a, k)
		a["pos"] = door_pos
		a["alpha"] = 0.0
		walk_to(id, wait, t0 + float(k) * 0.5, 2.5, {"state": "look", "from": 0.0, "until": NO_END})
		k += 1
	for s in _sils:
		if s["group"] == group:
			s["present"] = true


func gatherers_enter(t0: float, all := true) -> void:
	var k := 0
	for id in ids_of("gatherers"):
		var a: Dictionary = actors[id]
		if all or bool(a["data"].get("stays_on_bad", false)):
			if not a["present"]:  # never gathered at the door (or a room without one): they walk in now, visibly
				a["present"] = true
				a["alpha"] = 0.0
				a["pos"] = door_pos + Vector2(float(k % 3) * 0.3, 0.0)
				if str(a["data"].get("enter_from", "doorway")) == "side":
					a["pos"] = _side_start(a)
			walk_to(id, a["home"], t0 + float(k) * 0.35, 4.0)
			a["dir"] = {}
		elif not a["present"]:
			k += 1
			continue  # a dancer who never showed up does not appear just to leave
		else:
			var side: Vector2 = map.home(str(id)).get("side", a["home"])
			walk_to(id, side, t0 + float(k) * 0.35, 3.0, {"state": "look", "from": 0.0, "until": NO_END})
		k += 1
	if all:
		for s in _sils:
			if s["group"] == "gatherers":
				s["present"] = true


func step_back_some(t0: float) -> void:
	for id in ids_of("core"):
		var a: Dictionary = actors[id]
		if float(a["thresh"]) >= 4.0:
			var out: Vector2 = a["home"]
			out.x = clampf(out.x + (-1.4 if out.x < circle_c.x else 1.4), floor_x.x + 0.5, floor_x.y - 0.5)
			walk_to(id, out, t0, 2.5, {"state": "look", "from": 0.0, "until": t0 + 9.0})


func regroup(t0: float) -> void:
	for id in actors:
		var a: Dictionary = actors[id]
		if a["present"] and (a["pos"] as Vector2).distance_to(a["home"]) > 0.1:
			walk_to(id, a["home"], t0, 2.5)


func circle_form(t0: float, seconds := 3.5) -> void:
	var ids := ids_of("circle").filter(func(i: Variant) -> bool: return actors[str(i)]["present"])
	var n := maxi(ids.size(), 1)
	var gap := OPEN_GAP  # radians kept clear either side of the front: the circle opens towards the DJ so its centre stays in view
	var open_ang := circle_open.angle()  # the circle opens towards the map's `open` direction
	for k in ids.size():
		var ang := open_ang + gap + (TAU - 2.0 * gap) * float(k) / float(maxi(n - 1, 1))
		var pos := circle_c + Vector2(cos(ang) * circle_r.x, sin(ang) * circle_r.y)
		walk_to(str(ids[k]), pos, t0 + float(k) * 0.12, seconds, {"state": "dance", "from": 0.0, "until": NO_END})


func circle_scatter(t0: float, awkward := true) -> void:
	for id in ids_of("circle"):
		var a: Dictionary = actors[id]
		if not a["present"]:
			continue
		var out: Vector2 = a["home"]
		walk_to(id, out, t0, 3.0, {"state": "look" if awkward else "dance", "from": 0.0, "until": t0 + 8.0})


func hero_to(pos: Vector2, t0: float, seconds := 2.5, then: Dictionary = {}) -> void:
	for id in actors:
		if str(actors[id]["data"].get("role", "")) == "hero":
			walk_to(id, pos, t0, seconds, then)
			return


## The room is carried away (an abduction lifts, hellfire sinks): everyone present rises or falls by `dy` px over `seconds`, shrinking and fading.
func vanish_all(t0: float, seconds: float, dy: float, stagger := 0.12) -> void:
	var k := 0
	for id in _order:
		var a: Dictionary = actors[id]
		if not a["present"]:
			continue
		a["vanish"] = {"t0": t0 + float(k) * stagger, "t1": t0 + float(k) * stagger + seconds, "dy": dy}
		k += 1


## Where the hero stands in the middle of the circle, and where a soloist stands on the riser (the map's spots).
func centre_spot() -> Vector2:
	return circle_c


func solo_spot() -> Vector2:
	return riser_spot


func hero_node() -> StoryCharacter:
	for id in actors:
		if str(actors[id]["data"].get("role", "")) == "hero":
			return actors[id]["node"]
	return null


func hero_id() -> String:
	for id in actors:
		if str(actors[id]["data"].get("role", "")) == "hero":
			return id
	return ""


func set_ending(key: String) -> void:
	_ending = data.tableau_of(key) if key != "" else ""
	for id in actors:
		actors[id]["dir"] = {}


## The two-bar result's local reaction (the persistent mood is the energy): a share of the room cheers or looks uncertain.
func react(passed: bool, grade: String, t0: float) -> void:
	var ids := present_ids()
	var share: float = float({"sharp": 0.6, "steady": 0.45, "loose": 0.3}.get(grade, 0.0)) if passed else 0.45
	for k in ids.size():
		if _rng.randf() > share:
			continue
		var a: Dictionary = actors[ids[k]]
		if str(a["lock"]) != "" or not _dancing_here(a) or _acted(a, t0):
			continue
		if passed:
			a["dir"] = {"state": "cheer" if energy > 45.0 else "dance", "from": t0, "until": t0 + 1.4, "sync": false}
		else:
			a["dir"] = {"state": "look" if energy > 25.0 else "sad", "from": t0, "until": t0 + 1.6, "sync": false}
