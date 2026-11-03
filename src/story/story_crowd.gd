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

var assets: StoryAssets
var data: StoryData
var bpm := 174.0
var reduced := false
var energy := 45.0
var glow_on := false
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


func setup(p_assets: StoryAssets, p_data: StoryData) -> void:
	assets = p_assets
	data = p_data
	_rng.seed = 4242
	var dw: Array = assets.anchor("doorway", [120, 250, 70, 110])
	door_pos = Vector2(float(dw[0]) + float(dw[2]) * 0.5, float(dw[1]) + float(dw[3]))
	var cc: Array = assets.anchor("circle_centre", [640, 380])
	circle_c = Vector2(float(cc[0]), float(cc[1]))
	var cr: Array = assets.anchor("circle_radii", [200, 60])
	circle_r = Vector2(float(cr[0]), float(cr[1]))
	var arch: Dictionary = assets.manifest.get("archetypes", {})
	var n := 0
	for a in data.actors:
		var ad: Dictionary = arch.get(str(a["archetype"]), {})
		var rig: Dictionary = ad.get("variants", {}).get(str(a["variant"]), {})
		if rig.is_empty():
			continue
		var c := StoryCharacter.new()
		c.name = str(a["id"])
		c.setup(assets, rig, str(a["id"]), 1000 + n)
		c.glow = bool(a.get("glow", false)) or (n % 4 == 0)
		c.glow_color = [Color(0.4, 1.0, 0.95), Color(1.0, 0.4, 0.85), Color(1.0, 0.8, 0.3)][n % 3]
		add_child(c)
		var present := str(a["group"]) == "core"
		actors[str(a["id"])] = {"node": c, "data": a, "home": _home_of(a), "pos": _home_of(a), "present": present, "move": {}, "dir": {},
			"thresh": float(a.get("thresh", 0.0)), "alpha": 1.0 if present else 0.0, "stay": false}
		n += 1
	_order = actors.keys()
	for s in data.silhouettes:
		var shape: Dictionary = assets.manifest.get("silhouettes", {}).get(str(s["shape"]), {})
		if shape.is_empty():
			continue
		var f := assets.floor_at(float(s["depth"]))
		_sils.append({"idle": assets._entry(shape.get("idle", {})), "up": assets._entry(shape.get("up", {})), "x": float(s["x"]),
			"y": float(f["y"]), "scale": float(f["scale"]) * 0.95, "group": str(s["group"]), "thresh": float(s["thresh"]),
			"present": str(s["group"]) == "core", "alpha": 1.0 if str(s["group"]) == "core" else 0.0, "ph": _rng.randf()})
	_resort()


func _home_of(a: Dictionary) -> Vector2:
	var f := assets.floor_at(float(a["depth"]))
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
		(a["node"] as StoryCharacter).sync = false
	for s in _sils:
		s["present"] = s["group"] == "core"
		s["alpha"] = 1.0 if s["present"] else 0.0
	glow_on = false
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
	_order.sort_custom(func(x: String, y: String) -> bool: return (actors[x]["pos"] as Vector2).y < (actors[y]["pos"] as Vector2).y)
	for i in _order.size():
		move_child(actors[_order[i]]["node"], i)


# --- per frame -------------------------------------------------------------------------------------------------------

func update(t: float, p_energy: float) -> void:
	energy = p_energy
	var e01 := clampf(energy / 100.0, 0.0, 1.0)
	var need_sort := false
	for id in _order:
		var a: Dictionary = actors[id]
		var c: StoryCharacter = a["node"]
		var mv: Dictionary = a["move"]
		var walking := false
		if not mv.is_empty():
			var u := clampf((t - float(mv["t0"])) / maxf(float(mv["t1"]) - float(mv["t0"]), 0.001), 0.0, 1.0)
			if t >= float(mv["t0"]):
				var ue := u * u * (3.0 - 2.0 * u)
				a["pos"] = (mv["from"] as Vector2).lerp(mv["to"], ue)
				walking = u < 1.0
				need_sort = true
				if u >= 1.0:
					a["move"] = {}
					if mv.get("hide_after", false):
						a["present"] = false
					if mv.has("then"):
						a["dir"] = mv["then"]
		var vis_target := 1.0 if a["present"] else 0.0
		a["alpha"] = move_toward(float(a["alpha"]), vis_target, 0.08 if reduced else 0.1)
		c.visible = float(a["alpha"]) > 0.01
		if not c.visible:
			continue
		var f := assets.floor_at(0.0)
		var depth_scale := _scale_at((a["pos"] as Vector2).y)
		c.position = a["pos"]
		c.scale = Vector2(depth_scale, depth_scale)
		c.modulate = Color(1, 1, 1, float(a["alpha"]))
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
		s["alpha"] = move_toward(float(s["alpha"]), 1.0 if s["present"] else 0.0, 0.1)
	if need_sort:
		_resort()
	queue_redraw()


func _scale_at(y: float) -> float:
	var rows: Array = assets.anchor("floor_rows", [])
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
		"legendary_set":
			return "cheer" if int(a["data"]["x"]) % 3 != 0 else "hands_up"
		"good_night":
			return "clap" if int(a["data"]["x"]) % 2 == 0 else "dance"
		_:
			return "sad" if int(a["data"]["x"]) % 3 != 0 else ("clap" if int(a["data"]["x"]) % 6 == 0 else "look")


func _draw() -> void:
	var e := energy
	for s in _sils:
		if float(s["alpha"]) < 0.02:
			continue
		var up: bool = e + float(s["thresh"]) > SIL_UP_E or _ending in ["legendary_set"]
		var ent: Dictionary = s["up"] if up else s["idle"]
		if ent.is_empty() or ent["tex"] == null:
			continue
		var t := float(Time.get_ticks_msec()) * 0.0  # placeholder, replaced by song time below
		var sway := sin((_t_now * bpm / 60.0 * 0.5 + float(s["ph"])) * TAU) * (2.0 + e * 0.05)
		var bob := absf(sin((_t_now * bpm / 60.0 + float(s["ph"])) * PI)) * (1.0 + e * 0.07) if e > 30.0 else 0.0
		var sc := float(s["scale"]) * float(ent["scale"])
		draw_set_transform(Vector2(float(s["x"]) + sway, float(s["y"]) - bob), 0.0, Vector2(sc, sc))
		draw_texture(ent["tex"], -ent["pivot"], Color(0.55, 0.6, 0.85, float(s["alpha"])) if e < 30.0 else Color(0.75, 0.75, 1.0, float(s["alpha"])))
	draw_set_transform_matrix(Transform2D.IDENTITY)


var _t_now := 0.0


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
			var side := Vector2(float(a["data"].get("side_x", 60.0)), _home_of({"depth": float(a["data"].get("side_depth", 0.4))}).y)
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
	for k in ids.size():
		var ang := TAU * float(k) / float(n) + PI * 0.5
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


func hero_to(pos: Vector2, t0: float, seconds := 2.5) -> void:
	for id in actors:
		if str(actors[id]["data"].get("role", "")) == "hero":
			walk_to(id, pos, t0, seconds)
			return


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
	_ending = key
	for id in actors:
		actors[id]["dir"] = {}


## The two-bar result's local reaction (the persistent mood is the energy): a share of the room cheers or looks uncertain.
func react(passed: bool, grade: String, t0: float) -> void:
	var ids := present_ids()
	var share := {"sharp": 0.6, "steady": 0.45, "loose": 0.3}.get(grade, 0.0) if passed else 0.45
	for k in ids.size():
		if _rng.randf() > share:
			continue
		var a: Dictionary = actors[ids[k]]
		if passed:
			a["dir"] = {"state": "cheer" if energy > 45.0 else "dance", "from": t0, "until": t0 + 1.4, "sync": false}
		else:
			a["dir"] = {"state": "look" if energy > 25.0 else "sad", "from": t0, "until": t0 + 1.6, "sync": false}
