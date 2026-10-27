class_name BattleView
extends Control
## Fixed-camera view of the whole battlefield. Reads the simulation every frame; never advances it.
## Two sprite layers (one per faction, each with its own colour-remap material) and an effects layer on top.

const FACTION_BASE := [Color(0.35, 0.62, 1.0), Color(1.0, 0.36, 0.30)]
const SHOT_LIFE := 0.08
const HIT_LIFE := 0.3
const EXPLOSION_LIFE := 0.65

var sim: BattleSim
var bank := SpriteBank.new()
var cell := 45.0
var origin := Vector2.ZERO
var _layers: Array[Node2D] = []
var _fx: Node2D
var _effects: Array = []  # {kind, pos, t0, life, ...}
var _wall := 0.0
var _rotor := 0.0


func _ready() -> void:
	bank.load()
	var shader := load("res://src/ui/faction_remap.gdshader") as Shader
	for side in 2:
		var layer := _SideLayer.new()
		layer.view = self
		layer.side = side
		var mat := ShaderMaterial.new()
		mat.shader = shader
		mat.set_shader_parameter("src_ramp", _ramp_from(bank.remap_ramp))
		mat.set_shader_parameter("dst_ramp", _faction_ramp(FACTION_BASE[side]))
		layer.material = mat
		add_child(layer)
		_layers.append(layer)
	_fx = _FxLayer.new()
	_fx.view = self
	add_child(_fx)
	resized.connect(_layout)
	_layout()


func setup(p_sim: BattleSim) -> void:
	sim = p_sim
	_layout()


func _layout() -> void:
	if sim == null:
		return
	cell = floor(minf(size.x / sim.width, size.y / sim.height))
	origin = Vector2((size.x - cell * sim.width) * 0.5, (size.y - cell * sim.height) * 0.5)


func to_px(p: Vector2) -> Vector2:
	return origin + p * cell


func _ramp_from(rgb_list: Array) -> PackedVector3Array:
	var out := PackedVector3Array()
	for c in rgb_list:
		out.append(Vector3(float(c[0]) / 255.0, float(c[1]) / 255.0, float(c[2]) / 255.0))
	while out.size() < 16:
		out.append(Vector3.ZERO)
	return out


## A faction ramp with the same brightness steps as the gold source ramp.
func _faction_ramp(base: Color) -> PackedVector3Array:
	var out := PackedVector3Array()
	var src := _ramp_from(bank.remap_ramp)
	var top := src[0].length() if src.size() > 0 else 1.0
	for i in 16:
		var k: float = (src[i].length() / top) if i < src.size() else 0.5
		var c := Vector3(base.r, base.g, base.b) * k
		out.append(Vector3(clampf(c.x, 0.0, 1.0), clampf(c.y, 0.0, 1.0), clampf(c.z, 0.0, 1.0)))
	return out


func _process(delta: float) -> void:
	_wall += delta
	_rotor += delta * 30.0
	if sim == null:
		return
	for ev in _pending_events:
		_add_effect(ev)
	_pending_events.clear()
	var keep := []
	for fx in _effects:
		if _wall - fx["t0"] < fx["life"]:
			keep.append(fx)
	_effects = keep
	queue_redraw()
	for l in _layers:
		l.queue_redraw()
	_fx.queue_redraw()


var _pending_events: Array = []


## Feed presentation events from the match (shot, hit, destroyed...).
func push_events(events: Array) -> void:
	_pending_events.append_array(events)


func _add_effect(ev: Dictionary) -> void:
	match ev.get("kind", ""):
		"shot":
			_effects.append({"kind": "shot", "t0": _wall, "life": SHOT_LIFE, "from": Vector2(ev["x"], ev["y"]), "to": Vector2(ev["tx"], ev["ty"]), "weapon": ev["weapon"]})
		"hit":
			_effects.append({"kind": "hit", "t0": _wall, "life": HIT_LIFE, "pos": Vector2(ev["x"], ev["y"])})
		"destroyed":
			var big: bool = ev.get("role", "") in ["main", "factory", "barracks", "power", "pad", "turret", "aa", "sam"]
			_effects.append({"kind": "explosion", "t0": _wall, "life": EXPLOSION_LIFE * (1.6 if big else 1.0), "pos": Vector2(ev["x"], ev["y"]), "big": big})


func _draw() -> void:
	# ground
	draw_rect(Rect2(Vector2.ZERO, size), Color(0.18, 0.22, 0.15))
	if sim == null:
		return
	var field := Rect2(origin, Vector2(sim.width, sim.height) * cell)
	draw_rect(field, Color(0.22, 0.27, 0.18))
	for i in range(1, sim.width):
		var x := origin.x + i * cell
		draw_line(Vector2(x, origin.y), Vector2(x, origin.y + sim.height * cell), Color(0, 0, 0, 0.06))
	for j in range(1, sim.height):
		var y := origin.y + j * cell
		draw_line(Vector2(origin.x, y), Vector2(origin.x + sim.width * cell, y), Color(0, 0, 0, 0.06))
	var mid := origin.x + sim.width * cell * 0.5
	draw_line(Vector2(mid, origin.y), Vector2(mid, origin.y + sim.height * cell), Color(1, 1, 1, 0.08), 2.0)


class _SideLayer:
	extends Node2D
	var view: BattleView
	var side := 0

	func _draw() -> void:
		if view.sim == null:
			return
		var sim: BattleSim = view.sim
		# buildings first (ground), then units sorted by y, then aircraft
		var units: Array = []
		var aircraft: Array = []
		for e in sim.entities:
			if e.side != side:
				continue
			if e.kind == BattleSim.Kind.BUILDING:
				_draw_building(e)
			elif e.alive and e.kind == BattleSim.Kind.UNIT:
				units.append(e)
			elif e.alive and e.kind == BattleSim.Kind.AIRCRAFT:
				aircraft.append(e)
		units.sort_custom(func(a: BattleSim.Ent, b: BattleSim.Ent) -> bool: return a.y < b.y)
		for e in units:
			_draw_unit(e)
		for e in aircraft:
			_draw_aircraft(e)

	func _tex(path: String) -> Texture2D:
		return view.bank.texture(path)

	func _draw_building(e: BattleSim.Ent) -> void:
		var bank: SpriteBank = view.bank
		var state := "idle"
		if not e.alive:
			state = "damaged"
		elif e.hp * 2 < e.max_hp:
			state = "damaged"
		var frames := bank.building_frames(e.actor, state)
		if frames.is_empty():
			return
		var fps := bank.state_fps(e.actor, state)
		var idx := 0
		if fps > 0 and frames.size() > 1 and e.alive:
			idx = int(view._wall * fps) % frames.size()
		var tex := _tex(frames[idx])
		if tex == null:
			return
		var scale := view.cell / SpriteBank.RA_CELL_PX
		var size_px := Vector2(tex.get_width(), tex.get_height()) * scale
		# anchor the sprite's bottom-left to the footprint's bottom-left cell edge
		var foot_bl := view.to_px(Vector2(e.cx, e.cy + e.h))
		var top_left := Vector2(foot_bl.x, foot_bl.y - size_px.y)
		var tint := Color(1, 1, 1, 1) if e.alive else Color(0.35, 0.35, 0.35, 0.9)
		draw_texture_rect(tex, Rect2(top_left, size_px), false, tint)
		if e.alive and e.role == "turret":
			var tframe := SpriteBank.facing_index(e.turret_heading, 32)
			var ttex := _tex(SpriteBank.frame_path("gun", tframe))
			if ttex != null:
				draw_texture_rect(ttex, Rect2(top_left, size_px), false, tint)
		elif e.alive and e.role == "aa":
			var it := bank.item("agun")
			var tfiles: Array = it.get("states", {}).get("turret", {}).get("files", [])
			if not tfiles.is_empty():
				var tframe := SpriteBank.facing_index(e.turret_heading, tfiles.size())
				var ttex := _tex(tfiles[tframe])
				if ttex != null:
					var tsize := Vector2(ttex.get_width(), ttex.get_height()) * scale
					draw_texture_rect(ttex, Rect2(Vector2(top_left.x, top_left.y), tsize), false, tint)
		if e.alive and e.hp < e.max_hp:
			_health_bar(Vector2(top_left.x, top_left.y - 6), size_px.x, float(e.hp) / e.max_hp, e.repairing)

	func _draw_unit(e: BattleSim.Ent) -> void:
		var bank: SpriteBank = view.bank
		var it := bank.item(e.actor)
		if it.is_empty():
			return
		var scale := view.cell / SpriteBank.RA_CELL_PX
		var pos := view.to_px(e.center())
		var hotspot: Array = it.get("hotspot", [12, 12])
		var facings := int(it.get("facings", 32))
		var frame := SpriteBank.facing_index(e.heading, facings)
		if it.has("layers"):
			var l: Dictionary = it["layers"]
			var body := _tex(SpriteBank.frame_path(str(l["body_prefix"]), frame))
			var turret := _tex(SpriteBank.frame_path(str(l["turret_prefix"]), SpriteBank.facing_index(e.turret_heading, facings)))
			if body != null:
				_blit(body, pos, hotspot, scale)
			if turret != null:
				_blit(turret, pos, hotspot, scale)
		else:
			var idx := frame
			if e.role == "infantry":
				var run_start := int(it.get("run_start", 16))
				var run_len := int(it.get("run_length", 6))
				if e.moving:
					var anim := int(view._wall * 10.0 + e.id) % run_len
					idx = run_start + frame * run_len + anim
				else:
					idx = int(it.get("stand_start", 0)) + frame
			var tex := _tex(SpriteBank.frame_path(str(it["prefix"]), idx))
			if tex != null:
				_blit(tex, pos, hotspot, scale)
		if e.hp < e.max_hp:
			_health_bar(pos + Vector2(-view.cell * 0.4, -view.cell * 0.75), view.cell * 0.8, float(e.hp) / e.max_hp, false)

	func _draw_aircraft(e: BattleSim.Ent) -> void:
		var bank: SpriteBank = view.bank
		var it := bank.item(e.actor)
		if it.is_empty():
			return
		var scale := view.cell / SpriteBank.RA_CELL_PX
		var airborne := e.air in [BattleSim.Air.SORTIE, BattleSim.Air.RETURNING, BattleSim.Air.LANDING, BattleSim.Air.WAITING]
		var pos := view.to_px(e.center())
		var hotspot: Array = it.get("hotspot", [23, 24])
		var frame := SpriteBank.facing_index(e.heading, int(it.get("facings", 32)))
		var tex := _tex(SpriteBank.frame_path(str(it["prefix"]), frame))
		if tex == null:
			return
		if airborne:
			# shadow on the ground, body lifted
			_blit(tex, pos + Vector2(6, 10), hotspot, scale, Color(0, 0, 0, 0.35))
			pos += Vector2(0, -view.cell * 0.9 + sin(view._wall * 3.0 + e.id) * 2.0)
		_blit(tex, pos, hotspot, scale)
		if airborne or e.air == BattleSim.Air.REARMING:
			# rotor
			var r := view.cell * 0.45
			var a := view._rotor + e.id
			draw_line(pos + Vector2(cos(a), sin(a) * 0.5) * r, pos - Vector2(cos(a), sin(a) * 0.5) * r, Color(0.9, 0.9, 0.9, 0.7), 2.0)
		if e.hp < e.max_hp:
			_health_bar(pos + Vector2(-view.cell * 0.4, -view.cell * 0.8), view.cell * 0.8, float(e.hp) / e.max_hp, false)
		# ammo pips
		for i in e.ammo_max:
			var c := Color(1, 0.85, 0.3, 0.9) if i < e.ammo else Color(0, 0, 0, 0.5)
			draw_rect(Rect2(pos + Vector2(-view.cell * 0.4 + i * 5.0, view.cell * 0.45), Vector2(4, 4)), c)

	func _blit(tex: Texture2D, pos: Vector2, hotspot: Array, scale: float, tint: Color = Color.WHITE) -> void:
		var size_px := Vector2(tex.get_width(), tex.get_height()) * scale
		var top_left := pos - Vector2(float(hotspot[0]), float(hotspot[1])) * scale + Vector2(0, size_px.y * 0.25)
		draw_texture_rect(tex, Rect2(top_left, size_px), false, tint)

	func _health_bar(top_left: Vector2, width: float, frac: float, repairing: bool) -> void:
		draw_rect(Rect2(top_left, Vector2(width, 4)), Color(0, 0, 0, 0.6))
		var c := Color(0.3, 0.9, 0.3) if frac > 0.5 else (Color(0.95, 0.8, 0.2) if frac > 0.25 else Color(0.95, 0.3, 0.2))
		draw_rect(Rect2(top_left, Vector2(width * frac, 4)), c)
		if repairing:
			draw_rect(Rect2(top_left + Vector2(width - 6, -6), Vector2(6, 6)), Color(1, 1, 1, 0.8))


class _FxLayer:
	extends Node2D
	var view: BattleView

	func _draw() -> void:
		var bank: SpriteBank = view.bank
		var scale := view.cell / SpriteBank.RA_CELL_PX
		for fx in view._effects:
			var age: float = view._wall - fx["t0"]
			var k: float = age / fx["life"]
			match fx["kind"]:
				"shot":
					var a := view.to_px(fx["from"])
					var b := view.to_px(fx["to"])
					var col := Color(1, 0.95, 0.6, 1.0 - k)
					if str(fx["weapon"]).begins_with("Hellfire") or fx["weapon"] == "Nike":
						col = Color(1, 0.6, 0.3, 1.0 - k)
					draw_line(a, b, col, 2.0)
					draw_circle(a, 3.0, Color(1, 1, 0.8, 1.0 - k))
				"hit":
					var frames: Array = bank.item("piff").get("frames_godot", [])
					if not frames.is_empty():
						var tex := bank.texture(frames[mini(int(k * frames.size()), frames.size() - 1)])
						if tex != null:
							var sz := Vector2(tex.get_width(), tex.get_height()) * scale
							draw_texture_rect(tex, Rect2(view.to_px(fx["pos"]) - sz * 0.5, sz), false)
				"explosion":
					var frames: Array = bank.item("explosion").get("frames_godot", [])
					if not frames.is_empty():
						var tex := bank.texture(frames[mini(int(k * frames.size()), frames.size() - 1)])
						if tex != null:
							var s := scale * (2.0 if fx["big"] else 1.0)
							var sz := Vector2(tex.get_width(), tex.get_height()) * s
							draw_texture_rect(tex, Rect2(view.to_px(fx["pos"]) - sz * 0.5, sz), false)
