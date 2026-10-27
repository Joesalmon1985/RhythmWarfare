class_name BattleView
extends Control
## Fixed-camera view of the whole battlefield at native Red Alert pixel scale, drawn the way OpenRA draws it:
## terrain tiles, building bibs, buildings (idle / damaged-idle / make / production and resupply overlays), walls by
## adjacency, units with facing frames and animations, aircraft with rotor and shadow, projectiles, muzzle flashes,
## impact explosions, death animations, craters and smoke. Reads the simulation every frame; never advances it.

const PIXEL_SCALE := 1  # integer multiple of the native 24 px cell, so sprites keep every pixel
const FACTION_BASE := [Color(0.35, 0.62, 1.0), Color(1.0, 0.36, 0.30)]
const AIR_ALTITUDE_PX := 30.0
const DEAD_TINT := Color(0.45, 0.45, 0.45, 1.0)
const WORLD_PER_CELL := 1024.0

## Weapon -> presentation from mods/ra/weapons and the actor Armaments (docs/OPENRA_BEHAVIOUR_SPEC.md).
## muzzle: sequence of the shooter's own image; muzzle_forward: Armament LocalOffset x in world units;
## projectile: image drawn in flight ("" for instant hits); impact: explosion sequence where the round lands.
const WEAPON_FX := {
	"25mm": {"muzzle": "muzzle", "muzzle_forward": 768, "projectile": "50cal", "impact": "small_explosion"},
	"90mm": {"muzzle": "muzzle", "muzzle_forward": 720, "projectile": "120mm", "impact": "small_explosion"},
	"105mm": {"muzzle": "muzzle", "muzzle_forward": 768, "projectile": "120mm", "impact": "small_explosion"},
	"TurretGun": {"muzzle": "muzzle", "muzzle_forward": 512, "projectile": "120mm", "impact": "small_explosion"},
	"M1Carbine": {"muzzle": "", "muzzle_forward": 0, "projectile": "", "impact": "piff"},
	"HellfireAG": {"muzzle": "", "muzzle_forward": 0, "projectile": "dragon", "impact": "small_explosion"},
	"HellfireAA": {"muzzle": "", "muzzle_forward": 0, "projectile": "dragon", "impact": "med_explosion_air"},
	"Nike": {"muzzle": "muzzle", "muzzle_forward": 0, "projectile": "missile", "impact": "med_explosion_air"},
	"ZSU-23": {"muzzle": "muzzle", "muzzle_forward": 520, "projectile": "", "impact": "small_explosion_air"},
	"FireballLauncher": {"muzzle": "", "muzzle_forward": 512, "projectile": "fb1", "impact": "napalm"},
	"M60mg": {"muzzle": "muzzle", "muzzle_forward": 0, "projectile": "", "impact": "piff"},
	"Vulcan": {"muzzle": "muzzle", "muzzle_forward": 0, "projectile": "", "impact": "piffs"},
	"Grenade": {"muzzle": "", "muzzle_forward": 0, "projectile": "bomb", "impact": "small_explosion"},
	"Dragon": {"muzzle": "", "muzzle_forward": 0, "projectile": "dragon", "impact": "small_explosion"},
	"RedEye": {"muzzle": "", "muzzle_forward": 0, "projectile": "dragon", "impact": "med_explosion_air"},
	"Flamer": {"muzzle": "", "muzzle_forward": 0, "projectile": "fb3", "impact": "small_napalm"},
	"FLAK-23-AA": {"muzzle": "muzzle", "muzzle_forward": 520, "projectile": "", "impact": "small_explosion_air"},
	"FLAK-23-AG": {"muzzle": "muzzle", "muzzle_forward": 520, "projectile": "", "impact": "small_explosion"},
	"155mm": {"muzzle": "muzzle", "muzzle_forward": 768, "projectile": "120mm", "impact": "artillery_explosion"},
	"SCUD": {"muzzle": "", "muzzle_forward": 0, "projectile": "v2", "impact": "large_explosion"},
	"120mm": {"muzzle": "muzzle", "muzzle_forward": 768, "projectile": "120mm", "impact": "small_explosion"},
	"MammothTusk": {"muzzle": "", "muzzle_forward": 0, "projectile": "dragon", "impact": "small_explosion"},
}
const DEFAULT_FX := {"muzzle": "", "muzzle_forward": 0, "projectile": "", "impact": "piffs"}

var sim: BattleSim
var bank := SpriteBank.new()
var map: Dictionary = {}
var cell := 24.0
var origin := Vector2.ZERO
var _layers: Array[Node2D] = []
var _fx: Node2D
var _ground: Node2D
var _effects: Array = []  # {image, seq, pos(cells), heading, t0, life, side, layer, loop, lift}
var _decals: Array = []   # permanent craters and scorches: {image, seq, frame, pos}
var _wall := 0.0
var _pending: Array = []
var _anim_phase: Dictionary = {}  # entity id -> wall time the current animation started
var _ground_dirty := true


func _ready() -> void:
	bank.load()
	var shader := load("res://src/ui/faction_remap.gdshader") as Shader
	_ground = _GroundLayer.new()
	_ground.view = self
	add_child(_ground)
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
	map = sim.rules.map if sim.rules != null else {}
	_layout()


func _layout() -> void:
	if sim == null:
		return
	cell = SpriteBank.RA_CELL_PX * PIXEL_SCALE
	origin = Vector2(floor((size.x - cell * sim.width) * 0.5), floor((size.y - cell * sim.height) * 0.5))
	_ground_dirty = true


func to_px(p: Vector2) -> Vector2:
	return (origin + p * cell).floor()


func _ramp_from(rgb_list: Array) -> PackedVector3Array:
	var out := PackedVector3Array()
	for c in rgb_list:
		out.append(Vector3(float(c[0]) / 255.0, float(c[1]) / 255.0, float(c[2]) / 255.0))
	while out.size() < 16:
		out.append(Vector3.ZERO)
	return out


func _faction_ramp(base: Color) -> PackedVector3Array:
	var out := PackedVector3Array()
	var src := _ramp_from(bank.remap_ramp)
	var top := src[0].length() if src.size() > 0 else 1.0
	for i in 16:
		var k: float = (src[i].length() / top) if i < src.size() else 0.5
		var c := Vector3(base.r, base.g, base.b) * k
		out.append(Vector3(clampf(c.x, 0.0, 1.0), clampf(c.y, 0.0, 1.0), clampf(c.z, 0.0, 1.0)))
	return out


func push_events(events: Array) -> void:
	_pending.append_array(events)


func _process(delta: float) -> void:
	_wall += delta
	if sim == null:
		return
	for ev in _pending:
		_add_effect(ev)
	_pending.clear()
	var keep := []
	for fx in _effects:
		if _wall - float(fx["t0"]) < float(fx["life"]):
			keep.append(fx)
	_effects = keep
	if _ground_dirty:
		_ground_dirty = false
		_ground.queue_redraw()
	for l in _layers:
		l.queue_redraw()
	_fx.queue_redraw()


static func fx_for(weapon: String) -> Dictionary:
	return WEAPON_FX.get(weapon, DEFAULT_FX)


func seq_life(image: String, seq: String) -> float:
	var n := bank.length(image, seq)
	return maxf(0.05, n * bank.tick_ms(image, seq) / 1000.0)


func _anim(image: String, seq: String, pos: Vector2, heading: float, layer: int = 2, extra: Dictionary = {}) -> void:
	if not bank.has_sequence(image, seq):
		return
	var fx := {"image": image, "seq": seq, "pos": pos, "heading": heading, "t0": _wall, "life": seq_life(image, seq), "layer": layer, "lift": 0.0}
	for k in extra:
		fx[k] = extra[k]
	_effects.append(fx)


func _add_effect(ev: Dictionary) -> void:
	match str(ev.get("kind", "")):
		"shot":
			var shooter: BattleSim.Ent = sim.get_entity(int(ev["from"]))
			if shooter == null:
				return
			var fx := fx_for(str(ev["weapon"]))
			var seq := str(fx["muzzle"])
			if seq.is_empty() or not bank.has_sequence(shooter.actor, seq):
				return
			var heading := float(ev.get("heading", 0.0))
			var forward := float(fx["muzzle_forward"]) / WORLD_PER_CELL
			var pos := Vector2(float(ev["x"]), float(ev["y"])) + Vector2(cos(heading), sin(heading)) * forward
			var lift := AIR_ALTITUDE_PX if shooter.kind == BattleSim.Kind.AIRCRAFT else 0.0
			_anim(shooter.actor, seq, pos, heading, 2, {"lift": lift, "side": shooter.side})
		"impact":
			var fx := fx_for(str(ev["weapon"]))
			_anim("explosion", str(fx["impact"]), Vector2(float(ev["x"]), float(ev["y"])), 0.0)
		"destroyed":
			_ground_dirty = true
			var role := str(ev.get("role", ""))
			var pos := Vector2(float(ev["x"]), float(ev["y"]))
			var e: BattleSim.Ent = sim.get_entity(int(ev["id"]))
			if e == null:
				return
			if role == "infantry":
				var deaths: Array = []
				for i in range(1, 7):
					if bank.has_sequence(e.actor, "die%d" % i):
						deaths.append("die%d" % i)
				if not deaths.is_empty():
					var seq: String = deaths[e.id % deaths.size()]
					_anim(e.actor, seq, pos, e.heading, 1, {"side": e.side, "life": seq_life(e.actor, seq) + 2.0, "hold": true})
				return
			if e.kind == BattleSim.Kind.AIRCRAFT:
				_anim("explosion", "med_explosion_air", pos, 0.0, 2, {"lift": AIR_ALTITUDE_PX})
				_anim("explosion", "small_explosion", pos, 0.0)
				return
			if e.kind == BattleSim.Kind.UNIT:
				_anim("explosion", "med_explosion", pos, 0.0)
				_decals.append({"image": "craters", "seq": "cr%d" % (1 + e.id % 6), "frame": 0, "pos": pos})
				return
			# buildings: fireball, lasting smoke, a crater field under the footprint
			_anim("explosion", "building", pos, 0.0)
			_anim("smoke_m", "idle", pos + Vector2(0, -0.5), 0.0, 2, {"life": 8.0, "loop": true})
			for i in e.w:
				for j in e.h:
					if (i + j) % 2 == 0:
						_decals.append({"image": "craters", "seq": "cr%d" % (1 + (e.id + i * 3 + j) % 6), "frame": 0, "pos": Vector2(e.cx + i + 0.5, e.cy + j + 0.5)})
		"pad_built", "spawned":
			_anim_phase[int(ev["id"])] = _wall
			if str(ev["kind"]) == "pad_built":
				_ground_dirty = true


## Current animation frame index for a looping sequence.
func anim_index(image: String, seq: String, phase_key: int = -1) -> int:
	var n := bank.length(image, seq)
	if n <= 1:
		return 0
	var t := _wall - float(_anim_phase.get(phase_key, 0.0))
	return int(t * 1000.0 / bank.tick_ms(image, seq)) % n


## Draw one frame centred on `centre_px` (OpenRA draws frames centred on the actor), honouring the sequence offset.
func blit(canvas: CanvasItem, image: String, seq: String, heading: float, anim: int, centre_px: Vector2, tint: Color = Color.WHITE) -> void:
	var tex := bank.texture_for(image, seq, heading, anim)
	if tex == null:
		return
	_blit_tex(canvas, tex, centre_px + bank.offset(image, seq) * PIXEL_SCALE, tint)


func blit_frame(canvas: CanvasItem, image: String, seq: String, n: int, centre_px: Vector2, tint: Color = Color.WHITE) -> void:
	var tex := bank.texture_frame(image, seq, n)
	if tex == null:
		return
	_blit_tex(canvas, tex, centre_px + bank.offset(image, seq) * PIXEL_SCALE, tint)


func _blit_tex(canvas: CanvasItem, tex: Texture2D, centre_px: Vector2, tint: Color) -> void:
	var sz := Vector2(tex.get_width(), tex.get_height()) * PIXEL_SCALE
	canvas.draw_texture_rect(tex, Rect2((centre_px - sz * 0.5).floor(), sz), false, tint)


## Buildings: the sprite is centred horizontally on the footprint and its top row sits on the footprint's top row
## (OpenRA centres on the Dimensions rectangle with LocalCenterOffset; for this roster that is the same thing).
func blit_building(canvas: CanvasItem, image: String, seq: String, anim: int, e: BattleSim.Ent, tint: Color = Color.WHITE) -> void:
	var tex := bank.texture_for(image, seq, 0.0, anim)
	if tex == null:
		return
	var sz := Vector2(tex.get_width(), tex.get_height()) * PIXEL_SCALE
	var top_centre := to_px(Vector2(e.cx + e.w * 0.5, e.cy))
	var top_left := (top_centre - Vector2(sz.x * 0.5, 0) + bank.offset(image, seq) * PIXEL_SCALE).floor()
	canvas.draw_texture_rect(tex, Rect2(top_left, sz), false, tint)


func building_centre_px(e: BattleSim.Ent) -> Vector2:
	return to_px(Vector2(e.cx + e.w * 0.5, e.cy + e.h * 0.5))


func health_bar(canvas: CanvasItem, top_left: Vector2, width: float, frac: float, repairing: bool) -> void:
	canvas.draw_rect(Rect2(top_left, Vector2(width, 3)), Color(0, 0, 0, 0.6))
	var c := Color(0.3, 0.9, 0.3) if frac > 0.5 else (Color(0.95, 0.8, 0.2) if frac > 0.25 else Color(0.95, 0.3, 0.2))
	canvas.draw_rect(Rect2(top_left, Vector2(width * frac, 3)), c)
	if repairing and bank.has_sequence("allyrepair", "repair"):
		blit(canvas, "allyrepair", "repair", 0.0, anim_index("allyrepair", "repair"), top_left + Vector2(width * 0.5, 10))


class _GroundLayer:
	extends Node2D
	var view: BattleView

	func _draw() -> void:
		draw_rect(Rect2(Vector2.ZERO, view.size), Color(0.1, 0.12, 0.08))
		if view.sim == null:
			return
		var tiles: Array = view.map.get("tiles", [])
		var field := Rect2(view.origin, Vector2(view.sim.width, view.sim.height) * view.cell)
		if tiles.is_empty():
			draw_rect(field, Color(0.22, 0.27, 0.18))
		else:
			for y in mini(tiles.size(), view.sim.height):
				var row: Array = tiles[y]
				for x in mini(row.size(), view.sim.width):
					var t: Dictionary = row[x]
					var tex := view.bank.texture("res://assets/openra/%s-%04d.png" % [str(t.get("t", "clear1")), int(t.get("f", 0))])
					if tex != null:
						draw_texture_rect(tex, Rect2(view.to_px(Vector2(x, y)), Vector2(view.cell, view.cell)), false)
		for d in view._decals:
			view.blit_frame(self, d["image"], d["seq"], int(d["frame"]), view.to_px(d["pos"]))
		# bibs: the building's own 'bib' sequence as a strip of tiles whose last row is the footprint's bottom row
		for e in view.sim.entities:
			if e.kind != BattleSim.Kind.BUILDING or not e.alive or not view.bank.has_sequence(e.actor, "bib"):
				continue
			var n := view.bank.length(e.actor, "bib")
			var width := 3 if n >= 6 else (2 if n >= 2 else 1)
			var rows := maxi(1, n / width)
			for i in n:
				var cx := e.cx + i % width
				var cy := e.cy + e.h - 1 + i / width - (rows - 1) + (rows - 1)
				var centre := view.to_px(Vector2(cx + 0.5, cy + 0.5))
				view.blit_frame(self, e.actor, "bib", view.bank.frame_at(e.actor, "bib", 0, i), centre)
		for d in view.map.get("decorations", []):
			var img := str(d.get("image", ""))
			var seq := str(d.get("sequence", "idle"))
			if view.bank.has_sequence(img, seq):
				var c := view.to_px(Vector2(float(d["x"]) + float(d.get("w", 1)) * 0.5, float(d["y"]) + float(d.get("h", 1)) * 0.5))
				view.blit(self, img, seq, 0.0, 0, c)


class _SideLayer:
	extends Node2D
	var view: BattleView
	var side := 0

	func _draw() -> void:
		if view.sim == null:
			return
		var ordered: Array = []
		for e in view.sim.entities:
			if e.side == side and (e.kind == BattleSim.Kind.BUILDING or e.alive):
				ordered.append(e)
		ordered.sort_custom(_painter_order)
		for e in ordered:
			match e.kind:
				BattleSim.Kind.BUILDING:
					_draw_building(e)
				BattleSim.Kind.UNIT:
					_draw_unit(e)
				BattleSim.Kind.AIRCRAFT:
					_draw_aircraft(e)
		for fx in view._effects:
			if int(fx.get("layer", 2)) == 1 and int(fx.get("side", -1)) == side:
				var age: float = view._wall - float(fx["t0"])
				var n := view.bank.length(fx["image"], fx["seq"])
				var idx := mini(int(age * 1000.0 / view.bank.tick_ms(fx["image"], fx["seq"])), n - 1)
				view.blit(self, fx["image"], fx["seq"], float(fx["heading"]), idx, view.to_px(fx["pos"]))
		# muzzle flashes carry the faction remap too, so they are drawn in the side layer
		for fx in view._effects:
			if int(fx.get("layer", 2)) == 2 and int(fx.get("side", -1)) == side:
				var age: float = view._wall - float(fx["t0"])
				var n := view.bank.length(fx["image"], fx["seq"])
				var idx := int(age * 1000.0 / view.bank.tick_ms(fx["image"], fx["seq"]))
				if idx < n:
					view.blit(self, fx["image"], fx["seq"], float(fx["heading"]), idx, view.to_px(fx["pos"]) + Vector2(0, -float(fx.get("lift", 0.0))))

	static func _painter_order(a: BattleSim.Ent, b: BattleSim.Ent) -> bool:
		var a_air := a.kind == BattleSim.Kind.AIRCRAFT
		var b_air := b.kind == BattleSim.Kind.AIRCRAFT
		if a_air != b_air:
			return b_air
		var ya := float(a.cy + a.h) if a.kind == BattleSim.Kind.BUILDING else a.y
		var yb := float(b.cy + b.h) if b.kind == BattleSim.Kind.BUILDING else b.y
		return ya < yb

	func _draw_building(e: BattleSim.Ent) -> void:
		var bank: SpriteBank = view.bank
		var damaged := e.hp * 2 < e.max_hp
		if e.is_wall:
			_draw_wall(e, damaged)
			return
		var tint := Color.WHITE
		var seq := ""
		var anim := 0
		if not e.alive:
			seq = bank.pick(e.actor, ["dead", "damaged-idle", "idle"])
			if seq != "dead":
				tint = view.DEAD_TINT
		else:
			var since_make: float = view._wall - float(view._anim_phase.get(e.id, -100.0))
			var make_len := bank.length(e.actor, "make")
			if make_len > 0 and since_make < make_len * bank.tick_ms(e.actor, "make") / 1000.0:
				seq = "make"
				anim = mini(int(since_make * 1000.0 / bank.tick_ms(e.actor, "make")), make_len - 1)
			else:
				seq = bank.pick(e.actor, ["damaged-idle", "idle"] if damaged else ["idle"])
				anim = view.anim_index(e.actor, seq, e.id)
		if seq.is_empty():
			return
		view.blit_building(self, e.actor, seq, anim, e, tint)
		if e.alive and seq != "make":
			if _is_busy(e):
				var ov := bank.pick(e.actor, ["damaged-build-top", "damaged-active"] if damaged else ["build-top", "active"])
				if not ov.is_empty():
					view.blit_building(self, e.actor, ov, view.anim_index(e.actor, ov, e.id), e)
			var turret := bank.pick(e.actor, ["damaged-turret", "turret"] if damaged else ["turret"])
			if not turret.is_empty():
				view.blit(self, e.actor, turret, e.turret_heading, 0, view.building_centre_px(e))
			if damaged and bank.has_sequence("smoke_m", "idle"):
				view.blit(self, "smoke_m", "idle", 0.0, view.anim_index("smoke_m", "idle", e.id), view.to_px(Vector2(e.cx + e.w * 0.5, e.cy + 0.3)))
		if e.alive and e.hp < e.max_hp:
			view.health_bar(self, view.to_px(Vector2(e.cx, e.cy)) + Vector2(0, -5), e.w * view.cell, float(e.hp) / e.max_hp, e.repairing)

	func _is_busy(e: BattleSim.Ent) -> bool:
		var sim: BattleSim = view.sim
		match e.role:
			"factory":
				return sim.queue_has(e.side, "tank")
			"barracks":
				return sim.queue_has(e.side, "infantry")
			"pad":
				var a: BattleSim.Ent = sim.get_entity(int(sim.slots[e.side][e.slot]["aircraft"]))
				return a != null and a.alive and a.air == BattleSim.Air.REARMING
		return false

	func _draw_wall(e: BattleSim.Ent, damaged: bool) -> void:
		var mask := SpriteBank.wall_mask(_wall_at(e, 0, -1), _wall_at(e, 1, 0), _wall_at(e, 0, 1), _wall_at(e, -1, 0))
		var seq := view.bank.pick(e.actor, ["damaged-idle", "idle"] if (damaged or not e.alive) else ["idle"])
		if seq.is_empty():
			return
		var n := view.bank.frame_at(e.actor, seq, 0, mask)
		view.blit_frame(self, e.actor, seq, n, view.building_centre_px(e), Color.WHITE if e.alive else view.DEAD_TINT)

	func _wall_at(e: BattleSim.Ent, dx: int, dy: int) -> bool:
		var id: int = int(view.sim._blocked.get(Vector2i(e.cx + dx, e.cy + dy), -2))
		var o: BattleSim.Ent = view.sim.get_entity(id)
		return o != null and o.alive and o.is_wall and o.actor == e.actor and o.side == e.side

	func _draw_unit(e: BattleSim.Ent) -> void:
		var bank: SpriteBank = view.bank
		var c := view.to_px(e.center())
		if e.role == "infantry":
			var seq := "stand"
			var anim := 0
			if e.moving and bank.has_sequence(e.actor, "run"):
				seq = "run"
				anim = view.anim_index(e.actor, "run", e.id)
			elif e.target >= 0:
				var attack := bank.pick(e.actor, ["shoot", "throw"])
				if not attack.is_empty():
					seq = attack
					anim = view.anim_index(e.actor, seq, e.id)
			view.blit(self, e.actor, seq, e.heading, anim, c)
		else:
			view.blit(self, e.actor, "idle", e.heading, 0, c)
			if bank.has_sequence(e.actor, "turret"):
				view.blit(self, e.actor, "turret", e.turret_heading, 0, c)
		if e.hp < e.max_hp:
			view.health_bar(self, c + Vector2(-10, -14), 20, float(e.hp) / e.max_hp, false)

	func _draw_aircraft(e: BattleSim.Ent) -> void:
		var bank: SpriteBank = view.bank
		var airborne := e.air in [BattleSim.Air.SORTIE, BattleSim.Air.RETURNING, BattleSim.Air.LANDING, BattleSim.Air.WAITING]
		var ground := view.to_px(e.center())
		var body := ground
		if airborne:
			view.blit(self, e.actor, "idle", e.heading, 0, ground + Vector2(4, 6), Color(0, 0, 0, 0.45))
			body = ground + Vector2(0, -view.AIR_ALTITUDE_PX + sin(view._wall * 3.0 + e.id))
		view.blit(self, e.actor, "idle", e.heading, 0, body)
		var rotor := "rotor" if airborne else bank.pick(e.actor, ["slow-rotor", "rotor"])
		if bank.has_sequence(e.actor, rotor) and (airborne or e.air != BattleSim.Air.READY):
			view.blit(self, e.actor, rotor, e.heading, view.anim_index(e.actor, rotor, e.id), body)
		if e.hp < e.max_hp:
			view.health_bar(self, body + Vector2(-10, -16), 20, float(e.hp) / e.max_hp, false)
		for i in e.ammo_max:
			draw_rect(Rect2(body + Vector2(-10 + i * 3, 10), Vector2(2, 2)), Color(1, 0.85, 0.3, 0.9) if i < e.ammo else Color(0, 0, 0, 0.5))


class _FxLayer:
	extends Node2D
	var view: BattleView

	func _draw() -> void:
		var bank: SpriteBank = view.bank
		for p in view.sim.projectiles:
			var fx := BattleView.fx_for(str(p["weapon"]))
			var img := str(fx["projectile"])
			var pos := view.to_px(Vector2(float(p["x"]), float(p["y"])))
			var shooter: BattleSim.Ent = view.sim.get_entity(int(p["from"]))
			if shooter != null and shooter.kind == BattleSim.Kind.AIRCRAFT:
				pos.y -= view.AIR_ALTITUDE_PX * 0.5
			if not img.is_empty() and bank.has_sequence(img, "idle"):
				view.blit(self, img, "idle", float(p["heading"]), 0, pos)
		for fx in view._effects:
			if int(fx.get("layer", 2)) != 2 or fx.has("side"):
				continue
			var age: float = view._wall - float(fx["t0"])
			var n := bank.length(fx["image"], fx["seq"])
			var idx := int(age * 1000.0 / bank.tick_ms(fx["image"], fx["seq"]))
			if bool(fx.get("loop", false)):
				idx = idx % maxi(n, 1)
			elif idx >= n:
				continue
			var pos := view.to_px(fx["pos"]) + Vector2(0, -float(fx.get("lift", 0.0)))
			view.blit(self, fx["image"], fx["seq"], float(fx["heading"]), idx, pos)
