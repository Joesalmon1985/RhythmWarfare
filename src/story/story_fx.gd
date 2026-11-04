class_name StoryFx
extends RefCounted
## The nightclub's light and set effects as pure drawing functions of song time: moving-head fixtures and beams, haze bands, the
## LED screen, woofers, the disco ball, floor glow, ripples, the dance-circle ring, spotlight pools, confetti and the mood dimming.
## Called by StoryFxLayer; reads the stage's action state. No frame counters: everything derives from `stage.t_now`.

var stage: StoryStage
var assets: StoryAssets
var crowd: StoryCrowd
var view := "main"  # the room this effects pass draws
var _bursts: Array = []  # haze_burst start times
var _pulses: Array = []  # {t0, passed}
var _door_t0 := -1.0
var _points: Array = []
var _spr: Dictionary = {}
var _tiles: Array = []  # the LED floor (anchor led_tiles): {quad: PackedVector2Array, i, j, c: Vector2, h: float}
var _font: Font
var _floor_y := 400.0  # where the beams land: just below the middle crowd row of this room
const LED_CELL := 10.0  # design px per LED-screen dot


func setup(p_assets: StoryAssets) -> void:
	assets = p_assets
	for id in ["woofer", "fixture", "disco_ball", "door_open", "spot_pool", "haze_a", "haze_b", "glow", "beam", "vignette", "glowstick"]:
		_spr[id] = assets.sprite(id)
	_points = []
	for p in assets.anchor("light_points", [], view):
		_points.append(Vector2(float(p[0]), float(p[1])))
	if _points.is_empty():
		for i in 8:
			_points.append(Vector2(120.0 + 150.0 * i, 40.0))
	_font = ThemeDB.fallback_font
	var frows: Array = assets.anchor("floor_rows", [], view)
	if not frows.is_empty():
		_floor_y = float(frows[frows.size() / 2]["y"]) + 50.0
	_tiles = []
	var lt: Dictionary = assets.anchor("led_tiles", {}, view)
	if not lt.is_empty():
		var vp := Vector2(float(lt["vanishing_point"][0]), float(lt["vanishing_point"][1]))
		var fy := float(lt["far_y"])
		var fx: Array = lt["far_x"]
		var rows: Array = lt["rows"]
		for j in rows.size() - 1:
			for i in fx.size() - 1:
				var q := PackedVector2Array()
				for k in [[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]]:
					var y := float(rows[k[1]])
					q.append(Vector2(vp.x + (float(fx[k[0]]) - vp.x) * (y - vp.y) / (fy - vp.y), y))
				var h := fposmod(sin(float(i * 31 + j * 17) * 12.9898) * 43758.5453, 1.0)
				_tiles.append({"quad": q, "i": i, "j": j, "c": (q[0] + q[2]) * 0.5, "h": h})


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
	var p: Array = stage.palette_colors()
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
	var r: Array = assets.anchor("led_screen", [], view)
	if r.size() < 4:
		return Rect2()  # this room has no LED screen
	return Rect2(float(r[0]), float(r[1]), float(r[2]), float(r[3]))


# --- base layer: under the crowd ------------------------------------------------------------------------------------------

func draw_base_add(ci: CanvasItem) -> void:
	_draw_pieces(ci, "behind", "add")
	_draw_led_floor(ci)
	_draw_woofer_glow(ci)
	# light that lands on the floor goes under the dancers, so it never washes out their faces
	var t := stage.t_now
	_draw_floor_glow(ci, t, _e01(), _kick_pulse())
	_draw_spots(ci, t)
	_draw_ripples(ci, t)
	_draw_circle_ring(ci, t)
	_draw_pulses(ci, t)


## The lit dance floor: single LED tiles chase, ripple and flash on the beat (additive, under the crowd). Patterns follow the set:
## a ripple out of the circle at a drop or a passed sequence, a sweep with the light wave, diagonal chases at energy, a slow breathing
## when the room is quiet. Reduced effects keeps only the slow, smooth patterns.
func _draw_led_floor(ci: CanvasItem) -> void:
	if _tiles.is_empty():
		return
	var t := stage.t_now
	var e := _e01()
	var b := _beats()
	var beat := floorf(b)
	var kp := _kick_pulse()
	var lost := stage.tableau() == "lost"
	var level := (0.1 + 0.55 * e) * (0.25 if lost else 1.0) * (0.55 if stage.reduced else 1.0) * (0.5 if stage.high_contrast else 1.0)
	var ripple_t := -1.0
	for name in ["bass_reveal", "burst"]:
		if stage.is_active(name, t):
			ripple_t = maxf(ripple_t, stage.since(name, t))
	var last_pass := -INF
	for p in _pulses:
		if p["passed"] and float(p["t0"]) <= t:
			last_pass = maxf(last_pass, float(p["t0"]))
	var wave_u := stage.progress("light_wave", t)
	var cc := crowd.circle_c
	for tile in _tiles:
		var c: Vector2 = tile["c"]
		var h: float = tile["h"]
		var a := 0.0
		if stage.reduced:
			a = 0.35 * (0.5 + 0.5 * sin(TAU * (b / 8.0) + float(tile["i"]) * 0.6 + float(tile["j"]) * 0.4))
		elif e < 0.3:
			a = 0.4 * maxf(0.0, sin(TAU * (b / 8.0 + h)))
		else:  # diagonal chase stepping one tile per beat, plus a few random tiles kicking on the beat
			var lane := (int(tile["i"]) + int(tile["j"]) + int(beat)) % 4
			a = (0.75 if lane == 0 else 0.0) * (0.45 + 0.55 * kp)
			if fposmod(h * 7.0 + beat * 0.618, 1.0) < 0.12 + 0.18 * e:
				a = maxf(a, kp)
		var d := Vector2((c.x - cc.x) / 3.2, c.y - cc.y).length()  # perspective-flattened distance from the circle
		if ripple_t >= 0.0:
			a = maxf(a, 1.2 * exp(-pow((d - ripple_t * 110.0) / 26.0, 2.0)) * exp(-ripple_t * 0.35))
		if t - last_pass < 1.2:
			a = maxf(a, 0.8 * exp(-pow((d - (t - last_pass) * 160.0) / 22.0, 2.0)) * (1.0 - (t - last_pass) / 1.2))
		if wave_u >= 0.0:
			var wx := lerpf(-120.0, 1400.0, wave_u)
			a = maxf(a, exp(-pow((c.x - wx) / 90.0, 2.0)))
		a *= level
		if a < 0.01:
			continue
		ci.draw_colored_polygon(tile["quad"], Color(_pal(int(h * 8.0)), clampf(a, 0.0, 0.85)))


func _draw_woofer_glow(ci: CanvasItem) -> void:
	var ws: Array = assets.anchor("woofers", [], view)
	if ws.is_empty() or stage.tableau() == "lost":
		return
	var k := _kick_pulse() * (0.5 + 0.5 * _e01()) * (1.0 if stage.woofer_pump() else 0.35) * (0.4 if stage.reduced else 1.0)
	if k < 0.02:
		return
	for w in ws:
		_draw_sprite(ci, "glow", Vector2(float(w[0]), float(w[1])), Vector2.ONE * float(w[2]) * 2.6 / 128.0, 0.0, Color(_pal(1), 0.45 * k))


func draw_base(ci: CanvasItem) -> void:
	_draw_pieces(ci, "behind", "mix")
	_draw_led(ci)
	_draw_woofers(ci)
	_draw_fixtures(ci)
	_draw_ball(ci)
	_draw_door(ci)
	_draw_riser_column(ci)
	if stage.high_contrast:  # high contrast: the room steps back so the dancers and the notes stand out against it
		ci.draw_rect(Rect2(-400, -400, 2080, 1520), Color(0.0, 0.0, 0.03, 0.42))


## The scissor column under a raised riser (the platform sprite itself moves up with the lift).
func _draw_riser_column(ci: CanvasItem) -> void:
	var lift := stage.riser_lift(stage.t_now)
	var l := assets.layer("riser") if view == "main" else {}
	if lift < 0.5 or l.is_empty():
		return
	var pos := Vector2(float(l["pos"][0]), float(l["pos"][1]))
	var size := Vector2(float(l["size"][0]), float(l["size"][1]))
	var bottom := pos.y + size.y
	var top := bottom - lift
	var x0 := pos.x + size.x * 0.22
	var x1 := pos.x + size.x * 0.78
	var a := stage.riser_level(stage.t_now)
	ci.draw_rect(Rect2(x0, top, x1 - x0, lift), Color(0.05, 0.03, 0.14, a))
	var n := maxi(int(lift / 18.0), 1)
	for k in n:  # the scissor struts
		var y0 := top + lift * float(k) / float(n)
		var y1 := top + lift * float(k + 1) / float(n)
		ci.draw_line(Vector2(x0 + 6.0, y0), Vector2(x1 - 6.0, y1), Color(0.45, 0.35, 0.9, 0.8 * a), 3.0)
		ci.draw_line(Vector2(x1 - 6.0, y0), Vector2(x0 + 6.0, y1), Color(0.45, 0.35, 0.9, 0.8 * a), 3.0)
	var neon := Color(_pal(0), (0.5 + 0.5 * _kick_pulse()) * a)
	ci.draw_line(Vector2(x0, top), Vector2(x0, bottom), neon, 2.0)
	ci.draw_line(Vector2(x1, top), Vector2(x1, bottom), neon, 2.0)


func _draw_led(ci: CanvasItem) -> void:
	var r := _led_rect()
	if r.size == Vector2.ZERO:
		return
	var e := _e01()
	var dim := 0.35 if stage.tableau() == "lost" else lerpf(0.45, 1.0, e)
	ci.draw_rect(r, Color(0.015, 0.012, 0.05, 0.97))
	var b := _beats() * (0.5 if stage.reduced else 1.0)  # reduced effects: the screen moves at half speed, no kick flashes
	var kp := 0.0 if stage.reduced else _kick_pulse()
	var c0 := _pal(0)
	var c1 := _pal(1)
	var cols := maxi(int(r.size.x / LED_CELL), 4)
	var rows := maxi(int(r.size.y / LED_CELL), 3)
	var cw := r.size.x / float(cols)
	var chh := r.size.y / float(rows)
	var mode := stage.led_mode()
	var word := _led_word()
	ci.draw_rect(r.grow(-1.0), Color(0.1, 0.08, 0.22, 0.3))  # the unlit dots (the grid lines below separate them)
	if word == "":
		for j in rows:
			var v := (float(j) + 0.5) / float(rows)  # 0 top .. 1 bottom
			for i in cols:
				var val := _led_value(mode, (float(i) + 0.5) / float(cols), v, i, b, e, kp)
				if val >= 0.05:  # only lit dots cost a draw call
					ci.draw_rect(Rect2(r.position.x + float(i) * cw + 1.0, r.position.y + float(j) * chh + 1.0, cw - 2.0, chh - 2.0),
						Color(c0.lerp(c1, v).lightened(0.08 * val), dim * (0.3 + 0.7 * val)))
	var grid := Color(0.015, 0.012, 0.05, 1.0)
	for i in range(1, cols):
		var x := r.position.x + float(i) * cw
		ci.draw_line(Vector2(x, r.position.y), Vector2(x, r.end.y), grid, 2.0)
	for j in range(1, rows):
		var y := r.position.y + float(j) * chh
		ci.draw_line(Vector2(r.position.x, y), Vector2(r.end.x, y), grid, 2.0)
	if word != "":
		var fs := int(r.size.y * 0.42)
		var a := dim * (0.85 + 0.15 * kp)
		ci.draw_string_outline(_font, Vector2(r.position.x, r.get_center().y + fs * 0.36), word, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, fs, 6, Color(c1, 0.5 * a))
		ci.draw_string(_font, Vector2(r.position.x, r.get_center().y + fs * 0.36), word, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, fs, Color(c0.lightened(0.55), a))
	ci.draw_rect(r, Color(c1, 0.5 * dim), false, 2.0)


## The ending's word on the LED screen ("" while the set runs).
func _led_word() -> String:
	match stage.tableau():
		"legendary":
			return "ENCORE!"
		"good":
			return "THANK YOU"
		"lost":
			return "GOOD NIGHT"
	return ""


## Brightness 0..1 of the LED dot at (u, v) (0..1 across, 0 top .. 1 bottom) for a screen mode.
func _led_value(mode: String, u: float, v: float, i: int, b: float, e: float, kp: float) -> float:
	match mode:
		"eq":
			var h := 0.12 + 0.88 * absf(sin(b * PI * 0.5 * (1.0 + float(i % 20) * 0.11) + float(i) * 1.7)) * (0.35 + 0.65 * e)
			h = clampf(h * (0.8 + 0.3 * kp), 0.0, 1.0)
			return 1.0 if 1.0 - v < h else 0.0
		"bars":
			var k := int(v * 6.0)
			var ww := 0.2 + 0.8 * absf(sin(b * 0.5 + float(k) * 0.9))
			return 0.9 if absf(u - 0.5) < ww * 0.5 else 0.0
		"rings":
			var d := Vector2((u - 0.5) * 3.6, v - 0.5).length()
			var best := 0.0
			for k in 4:
				var rad := fposmod(b * 0.25 + float(k) * 0.25, 1.0) * 1.9
				best = maxf(best, (1.0 - rad / 1.9) * clampf(1.0 - absf(d - rad) / 0.09, 0.0, 1.0))
			return best
		"wave":
			var best2 := 0.0
			for k in 3:
				var y := 0.5 + sin(u * TAU * (1.5 + float(k)) + b * 1.3 + float(k)) * (0.36 - 0.08 * float(k)) * (0.5 + 0.5 * e)
				best2 = maxf(best2, clampf(1.0 - absf(v - y) / 0.09, 0.0, 1.0))
			return best2
	return 0.0


func _draw_woofers(ci: CanvasItem) -> void:
	var ws: Array = assets.anchor("woofers", [], view)
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
	if stage.reduced:  # reduced effects: the rig holds a calm fan that breathes over four bars, whatever the cue
		return (float(i) - 3.5) * 0.12 + 0.06 * sin(TAU * b / 16.0 + float(i) * 0.7)
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
	var p: Array = assets.anchor("disco_ball", [], view)
	if p.size() < 2:
		return
	_draw_sprite(ci, "disco_ball", Vector2(float(p[0]), float(p[1])), Vector2.ONE, 0.04 * sin(_beats() * 0.5), Color(1, 1, 1, 1))


func _draw_door(ci: CanvasItem) -> void:
	if view != "main" or not stage.is_active("doors_open", stage.t_now):  # the door_open sprite is placed for the main room's doorway
		return
	var dw: Array = assets.anchor("doorway", [], view)
	if dw.size() < 4:
		return
	var s: Dictionary = _spr.get("door_open", {})
	if s.is_empty() or s["tex"] == null:
		return
	var u := clampf((stage.t_now - _door_t0) / 1.2, 0.0, 1.0)
	var pos: Array = assets.manifest.get("stage", {}).get("sprites", {}).get("door_open", {}).get("pos", [dw[0], dw[1]])
	ci.draw_set_transform(Vector2(float(pos[0]), float(pos[1])), 0.0, Vector2(s["scale"], s["scale"]))
	ci.draw_texture(s["tex"], Vector2.ZERO, Color(1, 1, 1, u))
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


## The chapter's authored set pieces (assets/story/<chapter>/manifest.json stage.pieces), animated by song time. `z` is behind or
## front of the crowd; `blend` "add" pieces draw on the additive layers, the rest normally. pos/size are the design-space
## rectangle; `pivot` is the animation origin (design px relative to pos when a piece has a `blend`, else texture px).
func _draw_pieces(ci: CanvasItem, z: String, blend: String) -> void:
	for p in assets.pieces(view):
		if str(p.get("z", "behind")) != z or str(p.get("blend", "mix")) != blend:
			continue
		var st := stage.piece_state(str(p["id"]), stage.t_now)
		if not st["visible"]:
			continue
		var tex := assets.texture(str(p["file"]))
		if tex == null:
			continue
		var pos := Vector2(float(p["pos"][0]), float(p["pos"][1]))
		var size: Array = p.get("size", [tex.get_width() * 0.5, tex.get_height() * 0.5])
		var k0 := Vector2(float(size[0]) / tex.get_width(), float(size[1]) / tex.get_height())
		var piv_tex := Vector2.ZERO
		if p.has("pivot"):
			piv_tex = Vector2(float(p["pivot"][0]), float(p["pivot"][1]))
			if assets.pivot_in_design_px():  # design px relative to pos
				piv_tex = Vector2(piv_tex.x / maxf(k0.x, 0.0001), piv_tex.y / maxf(k0.y, 0.0001))
		var b := _beats()
		var a: float = float(st["alpha"])
		var rot := 0.0
		var k := k0
		match str(p.get("anim", "none")):
			"pulse":
				k *= 1.0 + 0.03 * _kick_pulse() + 0.06 * float(st["pulse"])
				a *= 0.78 + 0.22 * _kick_pulse() + 0.25 * float(st["pulse"])
			"flicker":
				a *= (0.7 + 0.3 * sin(b * 3.1 + pos.x) * sin(b * 1.7)) if not stage.reduced else 0.85
			"rotate":
				rot = b * (0.05 if stage.reduced else 0.12)
			"bob":
				pos.y += sin(b * 0.9) * 5.0
			"sway":
				rot = 0.05 * sin(b * 0.5 + pos.x)
		ci.draw_set_transform(pos + Vector2(piv_tex.x * k0.x, piv_tex.y * k0.y), rot, k)
		ci.draw_texture(tex, -piv_tex, Color(1, 1, 1, clampf(a, 0.0, 1.0)))
		ci.draw_set_transform_matrix(Transform2D.IDENTITY)


# --- additive light over the crowd ------------------------------------------------------------------------------------------

func draw_add(ci: CanvasItem) -> void:
	var t := stage.t_now
	var e := _e01()
	var kp := _kick_pulse()
	var inten := (0.18 + 0.6 * e) * (0.6 if stage.reduced else 1.0) * (0.55 if stage.high_contrast else 1.0)
	if stage.is_active("bass_reveal", t) or stage.is_active("burst", t):
		inten += 0.3
	if stage.lean_tableau() == "legendary" or stage.tableau() == "legendary":
		inten += 0.2
	if stage.tableau() == "lost":
		inten *= 0.25
	if stage.flickering(t):
		inten *= 0.35 + 0.3 * (0.5 + 0.5 * sin(t * 9.0)) if not stage.reduced else 0.4
	if stage.beam_mode() == "off":
		inten *= clampf(1.0 - (t - stage.beam_since()) / 0.6, 0.0, 1.0) if t - stage.beam_since() < 4.0 else 0.0
	var beam: Dictionary = _spr.get("beam", {})
	if not beam.is_empty() and beam["tex"] != null and inten > 0.01:
		var floor_y := _floor_y
		var bh := float(beam["tex"].get_height()) * float(beam["scale"])
		for i in _points.size():
			var p: Vector2 = _points[i]
			var ang := _fixture_angle(i, t)
			var len := maxf(floor_y - p.y, 120.0) / maxf(bh, 1.0)
			var col := _pal(i)
			var a := inten * (0.7 + 0.3 * kp * (0.3 if stage.reduced else 1.0))
			_draw_sprite(ci, "beam", p, Vector2(0.9 + 0.5 * e, len), ang, Color(col, clampf(a, 0.0, 0.9)))
	_draw_bloom(ci, t)
	_draw_spot_cones(ci, t)
	_draw_ball_dots(ci, t)
	_draw_pieces(ci, "front", "add")


## A drop lands: one soft bloom of light rising off the floor and fading over a second and a half (a single swell, never a flash).
func _draw_bloom(ci: CanvasItem, t: float) -> void:
	var since := INF
	for name in ["bass_reveal", "burst"]:
		if stage.is_active(name, t):
			since = minf(since, stage.since(name, t))
	if since > 1.6 or stage.tableau() == "lost":
		return
	var u := since / 1.6
	var a := (1.0 - u) * (1.0 - u) * (0.22 if stage.reduced else 0.45) * minf(since / 0.08, 1.0)
	var cc := crowd.circle_c
	_draw_sprite(ci, "glow", cc + Vector2(0, -40.0), Vector2(6.0 + 3.0 * u, 2.2 + 1.2 * u), 0.0, Color(_pal(0).lightened(0.3), a))
	_draw_sprite(ci, "glow", cc + Vector2(0, -120.0), Vector2(5.0, 4.0), 0.0, Color(1, 1, 1, a * 0.35))


var _floor_poly_cache := PackedVector2Array()


func _floor_poly() -> PackedVector2Array:
	if not _floor_poly_cache.is_empty():
		return _floor_poly_cache
	_floor_poly_cache = _build_floor_poly()
	return _floor_poly_cache


func _build_floor_poly() -> PackedVector2Array:
	var out := PackedVector2Array()
	for p in assets.anchor("floor_polygon", [[200, 330], [1080, 330], [1280, 460], [0, 460]], view):
		out.append(Vector2(float(p[0]), float(p[1])))
	return out


func _draw_floor_glow(ci: CanvasItem, t: float, e: float, kp: float) -> void:
	var a := (0.04 + 0.13 * e) * (0.5 + 0.5 * kp) * (0.4 if stage.reduced else 1.0)
	if stage.tableau() == "lost":
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


## The followspots' cones from the rig down to their pools (soft, over the crowd; the pools themselves are under it).
func _draw_spot_cones(ci: CanvasItem, t: float) -> void:
	var targets: Array = []
	if stage.is_active("spot_hero", t) and crowd.hero_id() != "":
		targets.append(crowd.actors[crowd.hero_id()]["pos"])
	if stage.is_active("spot_sweep", t):
		var u := stage.progress("spot_sweep", t)
		targets.append(Vector2(lerpf(160.0, 1120.0, u), 392.0 - 20.0 * sin(u * PI)))
	if stage.is_active("spot_circle", t):
		targets.append(crowd.circle_c + Vector2(0, 14))
	var beam: Dictionary = _spr.get("beam", {})
	if beam.is_empty() or beam["tex"] == null:
		return
	var bh := float(beam["tex"].get_height()) * float(beam["scale"])
	for p in targets:
		var top := Vector2(lerpf(640.0, (p as Vector2).x, 0.6), -12.0)
		var d: Vector2 = (p as Vector2) - top
		_draw_sprite(ci, "beam", top, Vector2(0.5, d.length() / maxf(bh, 1.0) * 1.15), -atan2(d.x, d.y), Color(1.0, 0.93, 0.75, 0.16 if stage.reduced else 0.24))


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
		if age < 0.0 or age > 0.7 or not p["passed"] or poly.size() < 3 or (not _tiles.is_empty() and not stage.reduced):
			continue
		ci.draw_colored_polygon(poly, Color(_pal(1), (1.0 - age / 0.7) * (0.12 if stage.reduced else 0.28)))


func _draw_ball_dots(ci: CanvasItem, t: float) -> void:
	if not stage.ball_on() or stage.reduced or stage.high_contrast:
		return
	var b := _beats()
	for i in 22:
		var ang := float(i) * 0.9 + b * 0.05
		var pos := Vector2(640.0 + cos(ang) * (120.0 + 440.0 * fposmod(float(i) * 0.137, 1.0)), 360.0 + sin(ang * 1.3) * 60.0)
		_draw_sprite(ci, "glow", pos, Vector2(0.22, 0.12), 0.0, Color(_pal(i), 0.5))


# --- normal-blend overlay: haze, confetti, mood dimming, vignette -----------------------------------------------------------

func draw_norm(ci: CanvasItem) -> void:
	_draw_pieces(ci, "front", "mix")
	var t := stage.t_now
	var e := _e01()
	var burst := 0.0
	for b0 in _bursts:
		if t >= float(b0):
			burst = maxf(burst, exp(-(t - float(b0)) / 3.2))
	var haze_a := (0.06 + 0.1 * e + 0.35 * burst) * (0.5 if stage.reduced else 1.0) * (0.35 if stage.high_contrast else 1.0)
	for k in 2:
		var s: Dictionary = _spr.get("haze_a" if k == 0 else "haze_b", {})
		if s.is_empty() or s["tex"] == null:
			continue
		var w: float = maxf(float(s["tex"].get_width()) * float(s["scale"]), 64.0)  # never a zero step in the tiling loop below
		var x := -fposmod(t * (9.0 + 5.0 * k) + float(k) * 300.0, w)
		var y := 230.0 + float(k) * 70.0
		var col := Color(0.7, 0.75, 1.0, haze_a)
		var xx := x
		if is_nan(xx):
			continue
		while xx < 1280.0:
			_draw_sprite(ci, "haze_a" if k == 0 else "haze_b", Vector2(xx, y), Vector2.ONE, 0.0, col)
			xx += w
	if stage.is_active("confetti", t):
		_draw_confetti(ci, t)
	var dim := 0.0
	if stage.tableau() == "lost":
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
