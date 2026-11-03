class_name StoryCrowd
extends Node2D
## The crowd on the fixed dance floor: rigged dancers (StoryCharacter) and cheap rear silhouettes, placed on the art's floor rows
## by depth, y-sorted, and driven by the crowd energy plus authored directives. Everything is a pure function of song time and
## the (deterministic) actions the director emits, so it pauses, restarts and fast-forwards exactly.
##
## Per dancer the state is: walking (arrival/exit), else an active directive (clap, cheer, look, ...), else the mood from the
## crowd energy plus the dancer's own threshold (so they react at different levels): sad < idle < dance < cheer.

const SIL_UP_E := 66.0
const NO_END := 1.0e9
const CHAR_SCALE := 0.8  # the art's front row is a 260 to 300 px dancer: 0.8 keeps the room visible behind a crowd of 30

var assets: StoryAssets
var view := "main"  # the room this crowd lives in (actors and silhouettes with that `view`)
var data: StoryData
var bpm := 174.0
var reduced := false
var energy := 45.0
var glow_on := false
var lit_id := ""  # the dancer a followspot is on (drawn a touch brighter)
var riser_pos := Vector2(-9999, -9999)  # where a performer stands on the riser, and how high it has lifted them
var riser_lift := 0.0
var actors: Dictionary = {}  # id -> {node, data, home: Vector2, pos: Vector2, present, depth, move: {}, dir: {}, thresh, scale}
var _order: Array = []
var _sils: Array = []
var _rng := RandomNumberGenerator.new()
var _floor_scale := 1.0
var door_pos := Vector2(160, 330)
var circle_c := Vector2(640, 380)
var circle_r := Vector2(200, 60)
var _ending := ""
var _flinch_until := -1.0
var glow_colors: Array = [Color(0.4, 1.0, 0.95), Color(1.0, 0.4, 0.85), Color(1.0, 0.8, 0.3)]


func setup(p_assets: StoryAssets, p_data: StoryData) -> void:
	assets = p_assets
	data = p_data
	_rng.seed = 4242
	var dw: Array = assets.anchor("doorway", [], view)
	if dw.size() < 4:  # a room without a doorway: arrivals walk in from the left edge
		dw = [-40, 280, 40, 0]
	door_pos = Vector2(float(dw[0]) + float(dw[2]) * 0.5, float(dw[1]) + float(dw[3]))
	var cc: Array = assets.anchor("circle_centre", [640, 380], view)
	circle_c = Vector2(float(cc[0]), float(cc[1]))
	var cr: Array = assets.anchor("circle_radii", [200, 60], view)
	circle_r = Vector2(float(cr[0]), float(cr[1]))
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
		actors[str(a["id"])] = {"node": c, "data": a, "home": _home_of(a), "pos": _home_of(a), "present": present, "move": {}, "dir": {},
			"thresh": float(a.get("thresh", 0.0)), "alpha": 1.0 if present else 0.0, "stay": false, "vanish": {}}
		n += 1
	_order = actors.keys()
	for s in data.silhouettes:
		if str(s.get("view", "main")) != view:
			continue
		var shape: Dictionary = assets.manifest.get("silhouettes", {}).get(str(s["shape"]), {})
		if shape.is_empty():
			continue
		var f := assets.floor_at(float(s["depth"]), view)
		_sils.append({"idle": assets._entry(shape.get("idle", {})), "up": assets._entry(shape.get("up", {})), "x": float(s["x"]),
			"y": float(f["y"]), "scale": float(f["scale"]) * 0.95, "group": str(s["group"]), "thresh": float(s["thresh"]),
			"present": str(s["group"]) == "core", "alpha": 1.0 if str(s["group"]) == "core" else 0.0, "ph": _rng.randf()})
	_resort()


func _home_of(a: Dictionary) -> Vector2:
	var f := assets.floor_at(float(a["depth"]), view)
	return Vector2(float(a["x"]), float(f["y"]))


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
	_resort()


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


func _resort() -> void:
	_order.sort_custom(_nearer)
	for i in _order.size():
		move_child(actors[_order[i]]["node"], i)


## Depth order: further back (smaller feet y) first; ties broken by x then id, so equal rows never swap places between frames.
func _nearer(x: String, y: String) -> bool:
	var px: Vector2 = actors[x]["pos"]
	var py: Vector2 = actors[y]["pos"]
	if not is_equal_approx(px.y, py.y):
		return px.y < py.y
	if not is_equal_approx(px.x, py.x):
		return px.x < py.x
	return x < y


# --- per frame -------------------------------------------------------------------------------------------------------

func update(t: float, p_energy: float) -> void:
	energy = p_energy
	var e01 := clampf(energy / 100.0, 0.0, 1.0)
	var need_sort := false
	if t < _last_t:  # a restart: fades start over
		_last_t = t
	var dt := clampf(t - _last_t, 0.0, 0.25) if _last_t > -INF else 0.0
	_last_t = t
	var fade := dt * (FADE_PER_S * (0.8 if reduced else 1.0))
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
				a["pos"] = (mv["from"] as Vector2).lerp(mv["to"], ue)
				walking = u < 1.0
				need_sort = true
				var dx: float = (mv["to"] as Vector2).x - (mv["from"] as Vector2).x
				c.walk_dir = clampf(dx / 60.0, -1.0, 1.0) * sin(PI * clampf(u * 1.4, 0.0, 1.0)) if walking else 0.0
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
		var depth_scale := _scale_at((a["pos"] as Vector2).y) * CHAR_SCALE
		var vn: Dictionary = a["vanish"]
		var vu := 0.0
		if not vn.is_empty() and t >= float(vn["t0"]):
			vu = clampf((t - float(vn["t0"])) / maxf(float(vn["t1"]) - float(vn["t0"]), 0.001), 0.0, 1.0)
		var lift := 0.0
		if riser_lift > 0.0 and (a["pos"] as Vector2).distance_to(riser_pos) < 30.0:
			lift = riser_lift
		c.position = (a["pos"] as Vector2) + Vector2(sin(vu * 9.0 + float(a["thresh"])) * 6.0 * vu, float(vn.get("dy", 0.0)) * vu * vu - lift)
		c.scale = Vector2(depth_scale, depth_scale) * (1.0 - 0.5 * vu) * (1.0 + 0.35 * lift / 72.0)  # a raised performer reads bigger
		var lit := 1.13 if id == lit_id else 1.0  # the followspot's dancer stands out from the crowd
		c.modulate = Color(lit, lit, lit * 0.97, float(a["alpha"]) * (1.0 - clampf((vu - 0.55) / 0.45, 0.0, 1.0)))
		c.reduced = reduced
		c.glow_on = glow_on and c.glow
		var dir: Dictionary = a["dir"]
		var st := _mood_state(a, e01)
		c.sync = false
		if walking:
			st = "walk"
		elif not dir.is_empty() and t < float(dir["until"]) and t >= float(dir.get("from", -1.0)):
			st = str(dir["state"])
			c.sync = bool(dir.get("sync", false))
		elif not dir.is_empty() and t >= float(dir["until"]):
			a["dir"] = {}
		if st != c.state:
			c.state = st
		c.update_pose(t, bpm, e01)
	for s in _sils:
		s["alpha"] = move_toward(float(s["alpha"]), 1.0 if s["present"] else 0.0, fade)
		var up_target := 1.0 if energy + float(s["thresh"]) > SIL_UP_E or _ending == "legendary" else 0.0
		s["upw"] = move_toward(float(s.get("upw", up_target)), up_target, dt * 3.0)
	if need_sort:
		_resort()
	queue_redraw()


func _scale_at(y: float) -> float:
	var rows: Array = assets.anchor("floor_rows", [], view)
	if rows.is_empty():
		return 0.55 + clampf((y - 300.0) / 140.0, 0.0, 1.0) * 0.45
	if y <= float(rows[0]["y"]):
		return float(rows[0]["scale"])
	for i in range(1, rows.size()):
		if y <= float(rows[i]["y"]):
			var u := (y - float(rows[i - 1]["y"])) / maxf(float(rows[i]["y"]) - float(rows[i - 1]["y"]), 0.001)
			return lerpf(float(rows[i - 1]["scale"]), float(rows[i]["scale"]), u)
	return float(rows[rows.size() - 1]["scale"])


func _mood_state(a: Dictionary, e01: float) -> String:
	var ee := energy + float(a["thresh"])
	if _ending != "":
		return _ending_state(a, ee)
	if ee < 18.0:
		return "sad"
	if ee < 32.0:
		return "idle"
	if ee < 70.0:
		return "dance"
	if ee < 88.0:
		return "dance" if (int(a["data"]["x"]) / 40) % 3 != 0 else "cheer"
	return "cheer"


func _ending_state(a: Dictionary, ee: float) -> String:
	match _ending:
		"legendary":
			return "cheer" if int(a["data"]["x"]) % 3 != 0 else "hands_up"
		"good":
			return "clap" if int(a["data"]["x"]) % 2 == 0 else "dance"
		_:
			return "sad" if int(a["data"]["x"]) % 3 != 0 else ("clap" if int(a["data"]["x"]) % 6 == 0 else "look")


func _draw() -> void:
	var e := energy
	var beats := _t_now * bpm / 60.0
	var rise := sin(PI * fposmod(beats, 1.0))  # the rear rows bounce on the beat like the dancers in front
	var tint := Color(0.55, 0.6, 0.85).lerp(Color(0.78, 0.76, 1.0), clampf((e - 20.0) / 30.0, 0.0, 1.0))
	for s in _sils:
		var al := float(s["alpha"])
		if al < 0.02:
			continue
		var sway := sin((beats * 0.25 + float(s["ph"])) * TAU) * (2.0 + e * 0.05)
		var bob := rise * (1.0 + e * 0.07) * clampf((e - 25.0) / 15.0, 0.0, 1.0)
		var upw := float(s.get("upw", 0.0))
		for k in 2:  # idle and hands-up cross-fade instead of popping
			var ent: Dictionary = s["up"] if k == 1 else s["idle"]
			var w := upw if k == 1 else 1.0 - upw
			if w < 0.01 or ent.is_empty() or ent["tex"] == null:
				continue
			var sc := float(s["scale"]) * float(ent["scale"])
			draw_set_transform(Vector2(float(s["x"]) + sway, float(s["y"]) - bob), 0.0, Vector2(sc, sc))
			draw_texture(ent["tex"], -ent["pivot"], Color(tint, al * w))
	draw_set_transform_matrix(Transform2D.IDENTITY)
	_draw_shadows()


## A soft contact shadow under every dancer (drawn before the dancers, which are this node's children), smaller and lighter while
## they are in the air, so feet sit on the floor instead of floating over it.
func _draw_shadows() -> void:
	if _shadow.is_empty():
		_shadow = assets.sprite("glow")
	if _shadow.is_empty() or _shadow["tex"] == null:
		return
	var tex: Texture2D = _shadow["tex"]
	for id in _order:
		var a: Dictionary = actors[id]
		var c: StoryCharacter = a["node"]
		if not c.visible or c.modulate.a < 0.05:
			continue
		var air := clampf(float(c.cur.get("jump", 0.0)) / 30.0, 0.0, 1.0)
		var w := 92.0 * c.scale.x * (1.0 - 0.35 * air)
		var feet := c.position + Vector2(float(c.cur.get("sway_x", 0.0)) * c.scale.x, 0.0)
		draw_texture_rect(tex, Rect2(feet - Vector2(w * 0.5, w * 0.13), Vector2(w, w * 0.26)), false,
			Color(0.0, 0.0, 0.04, 0.55 * c.modulate.a * (1.0 - 0.5 * air)))


var _shadow: Dictionary = {}


var _t_now := 0.0
var _last_t := -INF
const FADE_PER_S := 3.0  # arrivals and exits fade over a third of a second of song time


func set_time(t: float) -> void:
	_t_now = t


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
		if not a["present"]:
			continue
		a["dir"] = {"state": state, "from": t0 + float(k) * stagger, "until": t0 + seconds + float(k) * stagger, "sync": sync}
		k += 1


## A wave of `state` travelling left to right across the room over `seconds`, each dancer holding it for `hold` seconds.
func wave(t0: float, seconds: float, hold: float, state := "cheer") -> void:
	for id in present_ids():
		var a: Dictionary = actors[id]
		var u := clampf(float((a["pos"] as Vector2).x) / 1280.0, 0.0, 1.0)
		a["dir"] = {"state": state, "from": t0 + u * seconds, "until": t0 + u * seconds + hold, "sync": false}


func walk_to(id: String, to: Vector2, t0: float, seconds: float, then: Dictionary = {}, hide_after := false) -> void:
	if not actors.has(id):
		return
	var a: Dictionary = actors[id]
	a["move"] = {"from": a["pos"], "to": to, "t0": t0, "t1": t0 + seconds, "then": then, "hide_after": hide_after}


func bring_in(group: String, t0: float, seconds := 4.0, from_door := true) -> void:
	var k := 0
	for id in ids_of(group):
		var a: Dictionary = actors[id]
		if a["present"] and a["move"].is_empty():
			continue
		a["present"] = true
		var start: Vector2 = door_pos + Vector2(float(k % 3) * 10.0, 0.0)
		if str(a["data"].get("enter_from", "doorway")) == "side":
			start = Vector2(-60.0 if (a["home"] as Vector2).x < 640.0 else 1340.0, (a["home"] as Vector2).y)
		a["pos"] = start
		a["alpha"] = 0.0
		walk_to(id, a["home"], t0 + float(k) * 0.45, seconds)
		k += 1
	for s in _sils:
		if s["group"] == group:
			s["present"] = true


func gather_at_door(group: String, t0: float) -> void:
	var k := 0
	for id in ids_of(group):
		var a: Dictionary = actors[id]
		a["present"] = true
		var slot := int(a["data"].get("door_slot", k))
		var wait := door_pos + Vector2(float(slot % 4) * 34.0 - 10.0, 24.0 + float(slot / 4) * 22.0)
		a["pos"] = door_pos
		a["alpha"] = 0.0
		walk_to(id, wait, t0 + float(k) * 0.5, 2.5, {"state": "look", "from": 0.0, "until": NO_END})
		k += 1
	for s in _sils:
		if s["group"] == group:
			s["present"] = true
	_resort()


func gatherers_enter(t0: float, all := true) -> void:
	var k := 0
	for id in ids_of("gatherers"):
		var a: Dictionary = actors[id]
		if all or bool(a["data"].get("stays_on_bad", false)):
			walk_to(id, a["home"], t0 + float(k) * 0.35, 4.0)
			a["dir"] = {}
		else:
			var side := Vector2(float(a["data"].get("side_x", 60.0)), float(assets.floor_at(float(a["data"].get("side_depth", 0.4)), view)["y"]))
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
			out.x += (-90.0 if out.x < 640.0 else 90.0)
			walk_to(id, out, t0, 2.5, {"state": "look", "from": 0.0, "until": t0 + 9.0})


func regroup(t0: float) -> void:
	for id in actors:
		var a: Dictionary = actors[id]
		if a["present"] and (a["pos"] as Vector2).distance_to(a["home"]) > 4.0:
			walk_to(id, a["home"], t0, 2.5)


func circle_form(t0: float, seconds := 3.5) -> void:
	var ids := ids_of("circle").filter(func(i: Variant) -> bool: return actors[str(i)]["present"])
	var n := maxi(ids.size(), 1)
	var gap := 0.42  # radians kept clear either side of the front: the circle opens towards the DJ so its centre stays in view
	for k in ids.size():
		var ang := PI * 0.5 + gap + (TAU - 2.0 * gap) * float(k) / float(maxi(n - 1, 1))
		var pos := circle_c + Vector2(cos(ang) * circle_r.x, sin(ang) * circle_r.y)
		walk_to(str(ids[k]), pos, t0 + float(k) * 0.12, seconds, {"state": "dance", "from": 0.0, "until": NO_END})
	_resort()


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
		if passed:
			a["dir"] = {"state": "cheer" if energy > 45.0 else "dance", "from": t0, "until": t0 + 1.4, "sync": false}
		else:
			a["dir"] = {"state": "look" if energy > 25.0 else "sad", "from": t0, "until": t0 + 1.6, "sync": false}
