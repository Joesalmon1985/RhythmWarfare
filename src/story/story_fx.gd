class_name StoryFx
extends RefCounted
## The nightclub's light and set effects as pure drawing functions of song time: moving-head fixtures and beams, haze bands, the
## LED screen, woofers, the disco ball, floor glow, ripples, the dance-circle ring, spotlight pools, confetti and the mood dimming.
## Called by StoryFxLayer; reads the stage's action state. No frame counters: everything derives from `stage.t_now`.

var stage: StoryStage
var assets: StoryAssets
var crowd: StoryCrowd
var _bursts: Array = []  # haze_burst start times
var _pulses: Array = []  # {t0, passed}
var _door_t0 := -1.0
var _points: Array = []
var _spr: Dictionary = {}


func setup(p_assets: StoryAssets) -> void:
	assets = p_assets
	for id in ["woofer", "fixture", "disco_ball", "door_open", "spot_pool", "haze_a", "haze_b", "glow", "beam", "vignette", "glowstick"]:
		_spr[id] = assets.sprite(id)
	_points = []
	for p in assets.anchor("light_points", []):
		_points.append(Vector2(float(p[0]), float(p[1])))
	if _points.is_empty():
		for i in 8:
			_points.append(Vector2(120.0 + 150.0 * i, 40.0))


func reset() -> void:
	_bursts = []
	_pulses = []
	_door_t0 = -1.0


func update_fx(_t: float) -> void:
	pass


func haze_burst(t0: float) -> void:
	_bursts.append(t0)


func pulse(passed: bool, t0: float) -> void:
	if _pulses.size() > 6:
		_pulses.pop_front()
	_pulses.append({"t0": t0, "passed": passed})


func door_spill(t0: float) -> void:
	_door_t0 = t0


func _beats() -> float:
	return stage.t_now * stage.bpm / 60.0


func _e01() -> float:
	return clampf(stage.energy / 100.0, 0.0, 1.0)


func _pal(i: int) -> Color:
	var p: Array = StoryStage.PALETTES[stage.palette]
	return p[i % p.size()]


func _kick_pulse() -> float:
	var b := _beats()
	return exp(-7.0 * (b - floor(b)))


func _draw_sprite(ci: CanvasItem, id: String, pos: Vector2, scale: Vector2, rot: float, col: Color) -> void:
	var s: Dictionary = _spr.get(id, {})
	if s.is_empty() or s["tex"] == null:
		return
	var k: float = s["scale"]
	ci.draw_set_transform(pos, rot, Vector2(scale.x * k, scale.y * k))
	ci.draw_texture(s["tex"], -s["pivot"], col)
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


func _led_rect() -> Rect2:
	var r: Array = assets.anchor("led_screen", [440, 70, 400, 120])
	return Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))


# --- base layer: under the crowd ------------------------------------------------------------------------------------------

func draw_base(ci: CanvasItem) -> void:
	_draw_led(ci)
	_draw_woofers(ci)
	_draw_fixtures(ci)
	_draw_ball(ci)
	_draw_door(ci)


func _draw_led(ci: CanvasItem) -> void:
	var r := _led_rect()
	var e := _e01()
	var t := stage.t_now
	var dim := 0.35 if stage.ending() == "lost_the_floor" else lerpf(0.4, 1.0, e)
	ci.draw_rect(r, Color(0.02, 0.02, 0.07, 0.95))
	var b := _beats()
	var kp := _kick_pulse()
	var c0 := _pal(0)
	var c1 := _pal(1)
	match stage.led_mode():
		"eq":
			var n := 20
			var w := r.size.x / float(n)
			for i in n:
				var h := 0.12 + 0.88 * absf(sin(b * PI * 0.5 * (1.0 + float(i) * 0.11) + float(i) * 1.7)) * (0.35 + 0.65 * e)
				h = clampf(h * (0.8 + 0.3 * kp), 0.0, 1.0)
				var segs := int(h * 8.0)
				for s in segs:
					var sh := (r.size.y - 8.0) / 8.0
					var col := c0.lerp(c1, float(s) / 8.0)
					ci.draw_rect(Rect2(r.position.x + float(i) * w + 2.0, r.end.y - 4.0 - float(s + 1) * sh + 2.0, w - 4.0, sh - 3.0), Color(col, dim))
		"bars":
			for k in 6:
				var yy := r.position.y + 8.0 + float(k) * (r.size.y - 16.0) / 6.0
				var ww := r.size.x * (0.2 + 0.8 * absf(sin(b * 0.5 + float(k) * 0.9)))
				ci.draw_rect(Rect2(r.position.x + (r.size.x - ww) * 0.5, yy, ww, (r.size.y - 16.0) / 6.0 - 4.0), Color(c0.lerp(c1, float(k) / 6.0), dim))
		"rings":
			var cc := r.get_center()
			for k in 5:
				var rad := (fposmod(b * 0.25 + float(k) * 0.2, 1.0)) * r.size.y * 0.9
				ci.draw_arc(cc, rad, 0.0, TAU, 40, Color(c0.lerp(c1, float(k) / 5.0), dim * (1.0 - rad / (r.size.y * 0.9))), 3.0)
		"wave":
			for k in 3:
				var pts := PackedVector2Array()
				for x in 41:
					var u := float(x) / 40.0
					pts.append(Vector2(r.position.x + u * r.size.x, r.get_center().y + sin(u * TAU * (1.5 + k) + b * 1.3 + float(k)) * r.size.y * (0.28 - 0.06 * k) * (0.5 + 0.5 * e)))
				ci.draw_polyline(pts, Color(c0.lerp(c1, float(k) / 3.0), dim), 3.0)
	ci.draw_rect(r, Color(c1, 0.5 * dim), false, 2.0)


func _draw_woofers(ci: CanvasItem) -> void:
	var ws: Array = assets.anchor("woofers", [])
	var s: Dictionary = _spr.get("woofer", {})
	if ws.is_empty() or s.is_empty() or s["tex"] == null:
		return
	var base_r: float = float(s["tex"].get_width()) * 0.5 * float(s["scale"])
	var amp := 0.05 + (0.08 if stage.woofer_pump() else 0.0) + 0.04 * _e01()
	if stage.reduced:
		amp *= 0.5
	var bump := _kick_pulse() * amp
	for w in ws:
		var k := (float(w[2]) / maxf(base_r, 1.0)) * (1.0 + bump)
		_draw_sprite(ci, "woofer", Vector2(float(w[0]), float(w[1])), Vector2(k, k), 0.0, Color(1, 1, 1, 1))


func _fixture_angle(i: int, t: float) -> float:
	var b := _beats()
	var since := t - stage.beam_since()
	match stage.beam_mode():
		"sweep":
			return 0.55 * sin(TAU * b / 32.0 + float(i) * 0.8) * (0.5 if stage.reduced else 1.0)
		"fan":
			return (float(i) - 3.5) * 0.15 + 0.08 * sin(b * 0.4 + float(i))
		"cross":
			var dirn := 1.0 if i % 2 == 0 else -1.0
			return dirn * (0.15 + 0.4 * (0.5 + 0.5 * sin(TAU * b / 24.0)))
		_:
			return 0.1 * sin(float(i) + since * 0.3)


func _draw_fixtures(ci: CanvasItem) -> void:
	for i in _points.size():
		_draw_sprite(ci, "fixture", _points[i], Vector2.ONE, _fixture_angle(i, stage.t_now), Color(1, 1, 1, 1))


func _draw_ball(ci: CanvasItem) -> void:
	if not stage.ball_on():
		return
	var p: Array = assets.anchor("disco_ball", [640, 90])
	_draw_sprite(ci, "disco_ball", Vector2(float(p[0]), float(p[1])), Vector2.ONE, 0.04 * sin(_beats() * 0.5), Color(1, 1, 1, 1))


func _draw_door(ci: CanvasItem) -> void:
	if not stage.is_active("doors_open", stage.t_now):
		return
	var dw: Array = assets.anchor("doorway", [120, 250, 70, 110])
	var s: Dictionary = _spr.get("door_open", {})
	if s.is_empty() or s["tex"] == null:
		return
	var u := clampf((stage.t_now - _door_t0) / 1.2, 0.0, 1.0)
	var pos: Array = assets.manifest.get("stage", {}).get("sprites", {}).get("door_open", {}).get("pos", [dw[0], dw[1]])
	ci.draw_set_transform(Vector2(float(pos[0]), float(pos[1])), 0.0, Vector2(s["scale"], s["scale"]))
	ci.draw_texture(s["tex"], Vector2.ZERO, Color(1, 1, 1, u))
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


# --- additive light over the crowd ------------------------------------------------------------------------------------------

func draw_add(ci: CanvasItem) -> void:
	var t := stage.t_now
	var e := _e01()
	var kp := _kick_pulse()
	var inten := (0.18 + 0.6 * e) * (0.6 if stage.reduced else 1.0)
	if stage.is_active("bass_reveal", t) or stage.is_active("burst", t):
		inten += 0.3
	if stage.lean() == "legendary_set" or stage.ending() == "legendary_set":
		inten += 0.2
	if stage.ending() == "lost_the_floor":
		inten *= 0.25
	if stage.flickering(t):
		inten *= 0.35 + 0.3 * (0.5 + 0.5 * sin(t * 9.0)) if not stage.reduced else 0.4
	if stage.beam_mode() == "off":
		inten *= clampf(1.0 - (t - stage.beam_since()) / 0.6, 0.0, 1.0) if t - stage.beam_since() < 4.0 else 0.0
	var beam: Dictionary = _spr.get("beam", {})
	if not beam.is_empty() and beam["tex"] != null and inten > 0.01:
		var floor_y := 400.0
		var bh := float(beam["tex"].get_height()) * float(beam["scale"])
		for i in _points.size():
			var p: Vector2 = _points[i]
			var ang := _fixture_angle(i, t)
			var len := maxf(floor_y - p.y, 120.0) / maxf(bh, 1.0)
			var col := _pal(i)
			var a := inten * (0.55 + 0.45 * kp * (0.5 if stage.reduced else 1.0))
			_draw_sprite(ci, "beam", p, Vector2(0.9 + 0.5 * e, len), ang, Color(col, clampf(a, 0.0, 0.9)))
	_draw_floor_glow(ci, t, e, kp)
	_draw_spots(ci, t)
	_draw_ripples(ci, t)
	_draw_circle_ring(ci, t)
	_draw_pulses(ci, t)
	_draw_ball_dots(ci, t)


func _floor_poly() -> PackedVector2Array:
	var out := PackedVector2Array()
	for p in assets.anchor("floor_polygon", [[200, 330], [1080, 330], [1280, 460], [0, 460]]):
		out.append(Vector2(float(p[0]), float(p[1])))
	return out


func _draw_floor_glow(ci: CanvasItem, t: float, e: float, kp: float) -> void:
	var a := (0.04 + 0.13 * e) * (0.5 + 0.5 * kp) * (0.4 if stage.reduced else 1.0)
	if stage.ending() == "lost_the_floor":
		a *= 0.2
	var poly := _floor_poly()
	if poly.size() >= 3 and a > 0.003:
		ci.draw_colored_polygon(poly, Color(_pal(0), a))
	if stage.is_active("light_wave", t):
		var u := stage.progress("light_wave", t)
		var x := lerpf(-120.0, 1400.0, u)
		var g: Dictionary = _spr.get("glow", {})
		if not g.is_empty() and g["tex"] != null:
			for k in 6:
				_draw_sprite(ci, "glow", Vector2(x - float(k) * 70.0, 380.0 + 20.0 * sin(float(k))), Vector2(3.0, 1.6), 0.0, Color(_pal(k), 0.45 - 0.05 * k))


func _draw_spots(ci: CanvasItem, t: float) -> void:
	var pools: Array = []
	if stage.is_active("spot_hero", t) and crowd.hero_id() != "":
		var pos: Vector2 = crowd.actors[crowd.hero_id()]["pos"]
		pools.append([pos + Vector2(0, 6), Color(1.0, 0.92, 0.7, 0.75), 1.0])
	if stage.is_active("spot_sweep", t):
		var u := stage.progress("spot_sweep", t)
		pools.append([Vector2(lerpf(160.0, 1120.0, u), 392.0 - 20.0 * sin(u * PI)), Color(0.8, 0.9, 1.0, 0.65), 0.9])
	if stage.is_active("spot_circle", t):
		pools.append([crowd.circle_c + Vector2(0, 14), Color(1.0, 0.85, 0.5, 0.7), 1.5])
	for p in pools:
		_draw_sprite(ci, "spot_pool", p[0], Vector2(p[2], p[2]), 0.0, p[1])


func _draw_ripples(ci: CanvasItem, t: float) -> void:
	for name in ["floor_ripple", "bass_reveal"]:
		if not stage.is_active(name, t):
			continue
		var u := stage.progress(name, t)
		var cc := crowd.circle_c
		for k in 3:
			var q := fposmod(u * 2.0 + float(k) / 3.0, 1.0)
			var pts := PackedVector2Array()
			for s in 49:
				var a := TAU * float(s) / 48.0
				pts.append(cc + Vector2(cos(a) * q * 560.0, sin(a) * q * 150.0))
			ci.draw_polyline(pts, Color(_pal(k), (1.0 - q) * 0.7), 4.0)


func _draw_circle_ring(ci: CanvasItem, t: float) -> void:
	if not stage.is_active("circle", t):
		return
	var pts := PackedVector2Array()
	for s in 65:
		var a := TAU * float(s) / 64.0
		pts.append(crowd.circle_c + Vector2(cos(a) * crowd.circle_r.x * 1.12, sin(a) * crowd.circle_r.y * 1.12))
	var pulse := 0.5 + 0.5 * _kick_pulse()
	ci.draw_polyline(pts, Color(_pal(0), 0.35 + 0.3 * pulse), 5.0)
	ci.draw_polyline(pts, Color(1, 1, 1, 0.18 + 0.2 * pulse), 2.0)


func _draw_pulses(ci: CanvasItem, t: float) -> void:
	var poly := _floor_poly()
	for p in _pulses:
		var age: float = t - float(p["t0"])
		if age < 0.0 or age > 0.7 or not p["passed"] or poly.size() < 3:
			continue
		ci.draw_colored_polygon(poly, Color(_pal(1), (1.0 - age / 0.7) * (0.12 if stage.reduced else 0.28)))


func _draw_ball_dots(ci: CanvasItem, t: float) -> void:
	if not stage.ball_on() or stage.reduced:
		return
	var b := _beats()
	for i in 22:
		var ang := float(i) * 0.9 + b * 0.05
		var pos := Vector2(640.0 + cos(ang) * (120.0 + 440.0 * fposmod(float(i) * 0.137, 1.0)), 360.0 + sin(ang * 1.3) * 60.0)
		_draw_sprite(ci, "glow", pos, Vector2(0.22, 0.12), 0.0, Color(_pal(i), 0.5))


# --- normal-blend overlay: haze, confetti, mood dimming, vignette -----------------------------------------------------------

func draw_norm(ci: CanvasItem) -> void:
	var t := stage.t_now
	var e := _e01()
	var burst := 0.0
	for b0 in _bursts:
		if t >= float(b0):
			burst = maxf(burst, exp(-(t - float(b0)) / 3.2))
	var haze_a := (0.06 + 0.1 * e + 0.35 * burst) * (0.5 if stage.reduced else 1.0)
	for k in 2:
		var s: Dictionary = _spr.get("haze_a" if k == 0 else "haze_b", {})
		if s.is_empty() or s["tex"] == null:
			continue
		var w: float = float(s["tex"].get_width()) * float(s["scale"])
		var x := -fposmod(t * (9.0 + 5.0 * k) + float(k) * 300.0, maxf(w, 1.0))
		var y := 230.0 + float(k) * 70.0
		var col := Color(0.7, 0.75, 1.0, haze_a)
		var xx := x
		while xx < 1280.0:
			_draw_sprite(ci, "haze_a" if k == 0 else "haze_b", Vector2(xx, y), Vector2.ONE, 0.0, col)
			xx += w
	if stage.is_active("confetti", t):
		_draw_confetti(ci, t)
	var dim := 0.0
	if stage.ending() == "lost_the_floor":
		dim = 0.4
	else:
		dim = clampf(0.32 - e * 0.45, 0.0, 0.32)
	for p in _pulses:
		var age: float = t - float(p["t0"])
		if age >= 0.0 and age < 0.9 and not p["passed"] and not stage.reduced:
			dim += 0.12 * (1.0 - age / 0.9)
	if stage.flickering(t):
		dim += 0.15
	if dim > 0.005:
		ci.draw_rect(Rect2(0, 0, 1280, 720), Color(0.02, 0.02, 0.08, dim))
	var v: Dictionary = _spr.get("vignette", {})
	if not v.is_empty() and v["tex"] != null:
		ci.draw_texture_rect(v["tex"], Rect2(0, 0, 1280, 720), false, Color(1, 1, 1, 0.9))


func _draw_confetti(ci: CanvasItem, t: float) -> void:
	var u := stage.progress("confetti", t)
	if u < 0.0:
		return
	var age := u * 5.0
	var n := 24 if stage.reduced else 70
	for i in n:
		var h := fposmod(sin(float(i) * 12.9898) * 43758.5453, 1.0)
		var h2 := fposmod(sin(float(i) * 78.233) * 12345.678, 1.0)
		var x := 80.0 + h * 1120.0 + sin(age * 2.0 + float(i)) * 18.0
		var y := -30.0 + age * (80.0 + 120.0 * h2) - h2 * 120.0
		if y < -20.0 or y > 470.0:
			continue
		var col := _pal(i)
		ci.draw_set_transform(Vector2(x, y), age * (2.0 + h2 * 3.0) + float(i), Vector2(1, 0.6))
		ci.draw_rect(Rect2(-3, -4, 6, 8), Color(col.lightened(0.3), 1.0 - u * 0.5))
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)
