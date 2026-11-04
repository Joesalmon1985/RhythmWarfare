class_name StoryInterludeFx
extends Node2D
## The cutscene overlay drawn over the finished Night One club (design space): a UFO and tractor beam, or a crack in the floor, fire
## jets and a portal. Sprites come from the destination chapter's manifest ("interlude"); everything is a function of cutscene time.

var assets: StoryAssets  # the destination chapter's art
var kind := "abduction"
var t := 0.0
var events: Array = []
var energy_dim := 0.0


func ev(do: String) -> Dictionary:
	for e in events:
		if str(e["do"]) == do:
			return e
	return {}


func progress(do: String, dur_override := -1.0) -> float:
	var e := ev(do)
	if e.is_empty() or t < float(e["t"]):
		return -1.0
	var d := dur_override if dur_override > 0.0 else float(e.get("dur", 1.0))
	return clampf((t - float(e["t"])) / maxf(d, 0.001), 0.0, 1.0)


func _spr(id: String, pos: Vector2, scale: Vector2, rot: float, col: Color, additive := false) -> void:
	var s := assets.interlude_sprite(id)
	if s.is_empty() or s["tex"] == null:
		return
	var k: float = s["scale"]
	draw_set_transform(pos, rot, Vector2(scale.x * k, scale.y * k))
	draw_texture(s["tex"], -s["pivot"], col)
	draw_set_transform_matrix(Transform2D.IDENTITY)


func _draw() -> void:
	if assets == null:
		return
	match kind:
		"abduction":
			_draw_abduction()
		"awakening":
			_draw_awakening()
		"sectioned":
			_draw_sectioned()
		_:
			_draw_descent()


func _draw_abduction() -> void:
	var hover: Array = assets.interlude_anchor("ufo_hover", [640, 120])
	var floor_a: Array = assets.interlude_anchor("beam_floor", [640, 400])
	var du := progress("ufo_descend")
	if du < 0.0:
		return
	var ue := du * du * (3.0 - 2.0 * du)
	var pos := Vector2(float(hover[0]), lerpf(-260.0, float(hover[1]), ue) + sin(t * 1.4) * 4.0 * ue)
	var bu := progress("beam_on")
	if bu >= 0.0:
		var flick := 0.85 + 0.15 * sin(t * 11.0)
		var len := maxf(float(floor_a[1]) - pos.y, 100.0)
		var bs := assets.interlude_sprite("tractor_beam")
		if not bs.is_empty() and bs["tex"] != null:
			var h := float(bs["tex"].get_height()) * float(bs["scale"])
			_spr("tractor_beam", pos + Vector2(0, 40), Vector2(1.0 + 0.2 * sin(t * 3.0), len / maxf(h, 1.0)), 0.0, Color(1, 1, 1, clampf(bu * 1.4, 0.0, 1.0) * flick * 0.9))
		for i in 26:
			var h1 := fposmod(sin(float(i) * 12.9898) * 43758.5453, 1.0)
			var h2 := fposmod(sin(float(i) * 78.233) * 12345.678, 1.0)
			var yy := lerpf(float(floor_a[1]), pos.y + 60.0, fposmod(t * (0.25 + 0.3 * h2) + h1, 1.0))
			_spr("sparkle", Vector2(float(floor_a[0]) + (h1 - 0.5) * 340.0 * (yy / 500.0), yy), Vector2.ONE * (0.4 + 0.6 * h2), t * 2.0 + float(i), Color(1, 1, 1, 0.8 * bu))
	_spr("ufo_glow", pos + Vector2(0, 70), Vector2(1.2, 1.0), 0.0, Color(1, 1, 1, 0.7 * ue))
	_spr("ufo", pos, Vector2.ONE, 0.04 * sin(t * 0.9), Color(1, 1, 1, 1))
	var fu := progress("flood")
	if fu >= 0.0:
		var fs := assets.interlude_sprite("light_flood")
		if not fs.is_empty() and fs["tex"] != null:
			draw_texture_rect(fs["tex"], Rect2(-10, -10, 1300, 740), false, Color(1, 1, 1, clampf(fu * 1.2, 0.0, 1.0)))
		else:
			draw_rect(Rect2(-10, -10, 1300, 740), Color(0.9, 1.0, 0.95, clampf(fu * 1.2, 0.0, 1.0)))


func _draw_descent() -> void:
	var origin: Array = assets.interlude_anchor("crack_origin", [640, 420])
	var portal: Array = assets.interlude_anchor("portal_centre", [640, 360])
	var wu := progress("dim")
	if wu >= 0.0:
		var ws := assets.interlude_sprite("dark_wash")
		var col := Color(1, 1, 1, 0.55 * wu)
		if not ws.is_empty() and ws["tex"] != null:
			draw_texture_rect(ws["tex"], Rect2(-10, -10, 1300, 740), false, col)
		else:
			draw_rect(Rect2(-10, -10, 1300, 740), Color(0.3, 0.02, 0.02, 0.4 * wu))
	var cu := progress("crack_spread")
	if cu >= 0.0:
		_spr("crack_glow", Vector2(float(origin[0]), float(origin[1])), Vector2(0.3 + 1.1 * cu, 1.0), 0.0, Color(1, 1, 1, clampf(cu * 2.0, 0.0, 1.0) * (0.85 + 0.15 * sin(t * 7.0))))
	var fj := progress("fire_jets")
	if fj >= 0.0:
		for i in 5:
			var fx := float(origin[0]) + (float(i) - 2.0) * 190.0 + sin(float(i) * 3.1) * 40.0
			var show := clampf(fj * 5.0 - float(i) * 0.6, 0.0, 1.0)
			var fl := 0.8 + 0.2 * sin(t * 12.0 + float(i) * 2.0)
			_spr("flame_jet", Vector2(fx, float(origin[1]) + 40.0), Vector2(1.0, show * fl), 0.0, Color(1, 1, 1, show))
	var pu := progress("portal_open")
	if pu >= 0.0:
		var pe := pu * pu * (3.0 - 2.0 * pu)
		_spr("portal_vortex", Vector2(float(portal[0]), float(portal[1])), Vector2(1.0, 0.45) * (0.1 + 1.0 * pe), t * 0.9, Color(1, 1, 1, pe))
		for i in 30:
			var h1 := fposmod(sin(float(i) * 12.9898) * 43758.5453, 1.0)
			var h2 := fposmod(sin(float(i) * 78.233) * 12345.678, 1.0)
			var yy := lerpf(float(portal[1]) + 40.0, 60.0, fposmod(t * (0.2 + 0.25 * h2) + h1, 1.0))
			_spr("embers", Vector2(float(portal[0]) + (h1 - 0.5) * 700.0, yy), Vector2.ONE * (0.4 + h2), 0.0, Color(1, 1, 1, 0.7 * pe))
	var du := progress("wash")
	if du >= 0.0:
		draw_rect(Rect2(-10, -10, 1300, 740), Color(0.12, 0.0, 0.0, clampf(du * 1.2, 0.0, 1.0)))


func _full(col: Color) -> void:
	draw_rect(Rect2(-10, -10, 1300, 740), col)


## Waking in a hospital bed. The dream room warms and dissolves while a heartbeat starts to beep; the lids grow heavy and close in two
## drowsy blinks; in the dark a monitor trace sweeps across, its spikes landing on a heart rate that climbs as you come round, and the light
## through the lids swells on every beat; then the eyes flutter open onto your family leaning in over the bed, blurry at first and pulling
## into focus, before the morning light floods everything. Reduced effects: one smooth close and open, no flashes, a steady glow.
func _draw_awakening() -> void:
	var calm: bool = Session.reduced_effects
	# everything below is laid out on the screen (1280 x 720), whatever the cutscene stage's design-space fit
	var inv := get_global_transform().affine_inverse()
	var v0: Vector2 = inv * Vector2.ZERO
	var v1: Vector2 = inv * get_viewport_rect().size
	var base := Transform2D(0.0, (v1 - v0) / Vector2(1280.0, 720.0), 0.0, v0)
	draw_set_transform_matrix(base)
	var ce := ev("eyelids_close")
	var oe := ev("eyelids_open")
	var t_close := float(ce.get("t", 2.0))
	var d_close := maxf(float(ce.get("dur", 2.5)), 0.1)
	var t_open := float(oe.get("t", 11.0))
	var d_open := maxf(float(oe.get("dur", 3.0)), 0.1)
	# the heart: 56 bpm while dreaming, climbing to 92 as you wake; the beat phase is the closed-form integral of that rate
	var r0 := 56.0
	var r1 := 92.0
	var span := maxf(t_open + d_open - t_close, 0.1)
	var beat_at := func(tt: float) -> float:
		var u := clampf((tt - t_close) / span, 0.0, 1.0)
		var ramp := span * (u * u * u - 0.5 * u * u * u * u) + maxf(tt - t_close - span, 0.0)
		return (r0 * tt + (r1 - r0) * ramp) / 60.0
	var lub := exp(-fposmod(float(beat_at.call(t)), 1.0) * 9.0)  # the beep: a sharp swell on the beat, gone by the next
	var dream := clampf(t / (t_close + d_close), 0.0, 1.0)
	# 1. the dream dissolving: a warm veil thickens over the old room, the beeps faintly lighting it
	_full(Color(1.0, 0.8, 0.68, 0.5 * dream * dream))
	if not calm and t < t_close + d_close:
		_full(Color(0.7, 1.0, 0.85, 0.07 * lub * dream))
	# 2. behind the lids once they start to open: the family leaning in, out of focus, pulling sharp as the eyes adjust
	var ou := clampf((t - t_open) / d_open, 0.0, 1.0)
	if t >= t_open:
		var focus := clampf((ou - 0.2) / 0.8, 0.0, 1.0)
		focus = focus * focus * (3.0 - 2.0 * focus)
		var zoom := lerpf(1.08, 1.0, focus) + 0.012 * sin(t * 0.7)
		var rect := Rect2(640.0 - 650.0 * zoom, 360.0 - 370.0 * zoom, 1300.0 * zoom, 740.0 * zoom)
		var blur := assets.interlude_sprite("waking_blur")
		var sharp := assets.interlude_sprite("waking_view")
		if not blur.is_empty() and blur["tex"] != null:
			draw_texture_rect(blur["tex"], rect, false, Color(1, 1, 1, clampf(ou * 8.0, 0.0, 1.0)))
		if not sharp.is_empty() and sharp["tex"] != null:
			draw_texture_rect(sharp["tex"], rect, false, Color(1, 1, 1, focus))
		_full(Color(1.0, 0.97, 0.88, lerpf(0.72, 0.08, focus)))  # overexposed at first, the eyes adjusting
	# 3. the eyelids: two heavy, drowsy blinks going under; waking, a flutter (a crack of light, shut again, then open)
	var lid_keys: Array = []
	var lu := 0.0
	var c := 0.0
	if t >= t_close and t < t_close + d_close:
		lu = (t - t_close) / d_close
		lid_keys = [[0.0, 0.0], [1.0, 1.0]] if calm else [[0.0, 0.0], [0.24, 0.62], [0.4, 0.34], [0.68, 0.9], [0.8, 0.76], [1.0, 1.0]]
	elif t >= t_close + d_close and t < t_open:
		c = 1.0
	elif t >= t_open and t < t_open + d_open:
		lu = ou
		lid_keys = [[0.0, 1.0], [1.0, 0.0]] if calm else [[0.0, 1.0], [0.14, 0.7], [0.26, 0.97], [0.48, 0.42], [0.6, 0.56], [1.0, 0.0]]
	for i in range(1, lid_keys.size()):
		if lu <= float(lid_keys[i][0]):
			var ka: Array = lid_keys[i - 1]
			var kb: Array = lid_keys[i]
			var ks := (lu - float(ka[0])) / maxf(float(kb[0]) - float(ka[0]), 0.001)
			c = lerpf(float(ka[1]), float(kb[1]), ks * ks * (3.0 - 2.0 * ks))
			break
	var shut := clampf((c - 0.82) / 0.18, 0.0, 1.0)
	if c > 0.001:
		var top := assets.interlude_sprite("eyelid_top")
		var bot := assets.interlude_sprite("eyelid_bottom")
		if not bot.is_empty() and bot["tex"] != null:
			var hb := float(bot["tex"].get_height()) * float(bot["scale"])
			draw_texture_rect(bot["tex"], Rect2(-10, lerpf(790.0, 300.0, c), 1300, hb), false, Color(1, 1, 1, 1))
		if not top.is_empty() and top["tex"] != null:
			var ht := float(top["tex"].get_height()) * float(top["scale"])
			draw_texture_rect(top["tex"], Rect2(-10, lerpf(-90.0, 420.0, c) - ht, 1300, ht), false, Color(1, 1, 1, 1))
		if shut > 0.0:  # daylight through closed lids: a warm red glow that swells with every heartbeat
			var g := assets.sprite("glow")
			if not g.is_empty() and g["tex"] != null:
				var swell := 0.3 if calm else 0.14 + 0.3 * lub
				for k in 2:
					var sc := Vector2(11.0, 6.5) * (1.0 + 0.6 * float(k)) * float(g["scale"])
					draw_set_transform_matrix(base * Transform2D(0.0, sc, 0.0, Vector2(640, 380)))
					draw_texture(g["tex"], -g["pivot"], Color(1.0, 0.42 + 0.14 * float(k), 0.3, swell * shut * (0.55 - 0.2 * float(k))))
				draw_set_transform_matrix(base)
	# 4. the monitor in the dark: a phosphor trace swept left to right, one spike per heartbeat, fading behind the write head
	var me := ev("monitor")
	if not me.is_empty() and t >= float(me["t"]):
		var m0 := float(me["t"])
		var vis := clampf((t - m0) / 0.8, 0.0, 1.0) * (1.0 - clampf((t - (m0 + float(me.get("dur", 8.0)) - 0.8)) / 0.8, 0.0, 1.0))
		if t >= t_open:
			vis *= 1.0 - clampf((ou - 0.05) / 0.3, 0.0, 1.0)
		if vis > 0.01:
			var ecg := func(p: float) -> float:  # the trace height (px, up) at beat phase p: P wave, QRS on the whole beat, T wave
				var x := fposmod(p + 0.5, 1.0) - 0.5
				return 8.0 * exp(-pow((x + 0.13) / 0.035, 2.0)) - 12.0 * exp(-pow((x + 0.028) / 0.012, 2.0)) + 74.0 * exp(-pow(x / 0.014, 2.0)) \
					- 24.0 * exp(-pow((x - 0.028) / 0.012, 2.0)) + 14.0 * exp(-pow((x - 0.24) / 0.055, 2.0))
			var speed := 330.0  # px per second
			var tail := 1.9  # seconds of trace left glowing behind the write head
			var head := fposmod((t - m0) * speed, 1280.0)
			var runs: Array = []  # [points, fades] per unbroken stretch of the sweep
			var pts := PackedVector2Array()
			var fades := PackedFloat32Array()
			var n := int(tail * speed / 1.5)
			var last_x := -1.0
			for i in n + 1:
				var age := tail * (1.0 - float(i) / float(n))
				if t - age < m0:
					continue
				var x := head - age * speed
				if x < 0.0:
					x += 1280.0
				if x < last_x:  # the sweep wrapped round: close this stretch, start again at the left edge
					runs.append([pts, fades])
					pts = PackedVector2Array()
					fades = PackedFloat32Array()
				last_x = x
				pts.append(Vector2(x, 384.0 - float(ecg.call(beat_at.call(t - age))) * (0.75 if calm else 1.0)))
				fades.append(pow(1.0 - age / tail, 1.6))
			runs.append([pts, fades])
			var tc := Color(0.5, 1.0, 0.76)
			for pass_i in 3:
				var lw: float = [16.0, 7.0, 2.6][pass_i]
				var la: float = [0.1, 0.25, 0.95][pass_i]
				var lc := tc.lightened(0.55) if pass_i == 2 else tc
				for run in runs:
					var rp: PackedVector2Array = run[0]
					if rp.size() < 2:
						continue
					var cols := PackedColorArray()
					for fa in (run[1] as PackedFloat32Array):
						cols.append(Color(lc, la * fa * vis))
					draw_polyline_colors(rp, cols, lw)
			if pts.size() > 0:
				draw_circle(pts[pts.size() - 1], 10.0, Color(tc, 0.3 * vis))
				draw_circle(pts[pts.size() - 1], 3.6, Color(0.9, 1.0, 0.95, vis))
			var bpm := r0 + (r1 - r0) * clampf((t - t_close) / span, 0.0, 1.0)
			var hc := Color(0.55, 1.0, 0.78, vis * (0.6 + (0.0 if calm else 0.4 * lub)))
			var hp := Vector2(1072, 262)
			var hs := 10.0 * (1.0 + (0.0 if calm else 0.25 * lub))
			draw_colored_polygon(PackedVector2Array([hp + Vector2(0, hs * 0.9), hp + Vector2(-hs * 1.1, -hs * 0.1), hp + Vector2(-hs * 0.6, -hs * 0.8),
				hp + Vector2(0, -hs * 0.35), hp + Vector2(hs * 0.6, -hs * 0.8), hp + Vector2(hs * 1.1, -hs * 0.1)]), hc)
			var font := ThemeDB.fallback_font
			draw_string(font, Vector2(1092, 275), str(int(round(bpm))), HORIZONTAL_ALIGNMENT_LEFT, -1, 34, hc)
			draw_string(font, Vector2(1095, 296), "BPM", HORIZONTAL_ALIGNMENT_LEFT, -1, 14, Color(hc, hc.a * 0.7))
	# 5. the morning floods in
	var wu := progress("white")
	if wu >= 0.0:
		_full(Color(1.0, 0.97, 0.9, clampf(wu * 1.25, 0.0, 1.0)))
	draw_set_transform_matrix(Transform2D.IDENTITY)


## Coming to on a ward: the room goes soft and a gentle tunnel closes in (drifting off); cold, plain fluorescent light floods back as
## the tunnel opens again and the tubes overhead blink on one by one (never a strobe); a friendly ward door fades in, swings open onto
## the warm day room, and the camera walks through it into the new chapter. Events (interludes.json `sectioned`): tunnel, fluoro,
## tubes, door, door_open, walk_in, white (each {t, dur}); the scene itself handles caption, dim and fade_crowd.
func _draw_sectioned() -> void:
	var inv := get_global_transform_with_canvas().affine_inverse()
	var vr := get_viewport_rect()
	var p0: Vector2 = inv * vr.position
	var p1: Vector2 = inv * vr.end
	var view := Rect2(p0, p1 - p0).abs()  # the visible design-space rectangle (the cutscene stage is zoomed past the club's desk)
	var vc := view.get_center()
	var smooth := func(x: float) -> float: return x * x * (3.0 - 2.0 * x)
	# 1. drifting off: a soft dark tunnel closes in and breathes slowly; when the light comes it opens again
	var tu := progress("tunnel")
	var fu := progress("fluoro")
	var close := 0.0
	if tu >= 0.0:
		close = smooth.call(tu)
	if fu >= 0.0:
		close *= 1.0 - smooth.call(clampf(fu * 1.6, 0.0, 1.0))
	var wash_a := 0.0
	if fu >= 0.0:
		wash_a = 0.95 * smooth.call(clampf(fu * 2.0, 0.0, 1.0))
	var ws := assets.interlude_sprite("fluoro_wash")
	if wash_a > 0.002:
		if not ws.is_empty() and ws["tex"] != null:
			draw_texture_rect(ws["tex"], view.grow(12.0), false, Color(1, 1, 1, wash_a))
		else:
			draw_rect(view.grow(12.0), Color(0.86, 1.0, 0.95, wash_a))
		draw_rect(view.grow(12.0), Color(0.88, 1.0, 0.96, 0.5 * wash_a))  # plain, cold and bright: the room behind all but gone
		var adapt := clampf(1.0 - (t - float(ev("fluoro").get("t", 0.0))) / 2.5, 0.0, 1.0)  # eyes adjusting: the first moment is the brightest
		draw_rect(view.grow(12.0), Color(1.0, 1.0, 1.0, 0.35 * adapt * wash_a))
	# 2. the tubes overhead blink on, one after another, each with two soft dips (a gentle tink-tink, never a strobe)
	var tb := progress("tubes")
	if tb >= 0.0 and wash_a > 0.01:
		var row: Array = assets.interlude_anchor("tube_row", [[250, 40], [640, 40], [1030, 40]])
		var t_on := float(ev("tubes")["t"])
		for i in row.size():  # spread across what is on screen, at the top, like ceiling lights seen from a bed
			var tx := vc.x + (float(i) - float(row.size() - 1) * 0.5) * view.size.x * 0.32
			var lt := t - t_on - float(i) * 0.45
			if lt < 0.0:
				continue
			var b := clampf(lt / 0.25, 0.0, 1.0)
			b *= 1.0 - 0.5 * exp(-pow((lt - 0.32) / 0.07, 2.0)) - 0.4 * exp(-pow((lt - 0.62) / 0.08, 2.0))
			b *= 0.94 + 0.06 * sin(t * 2.3 + float(i))
			_spr("flicker_tube", Vector2(tx, view.position.y + 22.0 + absf(float(i) - 1.0) * 5.0), Vector2.ONE * 0.62, 0.0, Color(1, 1, 1, b * wash_a))
	if close > 0.002:
		var tv := assets.interlude_sprite("tunnel_vignette")
		var breathe := 1.0 + 0.03 * sin(t * 1.4)
		var k := lerpf(2.1, 0.85, close) * breathe  # 2.1x: the clear centre fills the screen; 0.85x: a narrow soft tunnel
		var sz := view.size * k
		if not tv.is_empty() and tv["tex"] != null:
			draw_texture_rect(tv["tex"], Rect2(vc - sz * 0.5, sz), false, Color(1, 1, 1, clampf(close * 1.4, 0.0, 1.0)))
			var cover := Rect2(vc - sz * 0.5, sz)
			for r in [Rect2(view.position.x - 20.0, view.position.y - 20.0, view.size.x + 40.0, cover.position.y - view.position.y + 20.0),
					Rect2(view.position.x - 20.0, cover.end.y, view.size.x + 40.0, view.end.y - cover.end.y + 20.0),
					Rect2(view.position.x - 20.0, cover.position.y, cover.position.x - view.position.x + 20.0, cover.size.y),
					Rect2(cover.end.x, cover.position.y, view.end.x - cover.end.x + 20.0, cover.size.y)]:
				if r.size.x > 0.0 and r.size.y > 0.0:  # beyond a shrunken tunnel texture: the same deep teal
					draw_rect(r, Color(0.04, 0.08, 0.13, clampf(close * 1.4, 0.0, 1.0) * 0.97))
		else:
			_full(Color(0.02, 0.06, 0.08, 0.6 * close))
	# 3. the friendly ward door: fades in, swings open onto the warm day room, and we walk through it
	var du := progress("door")
	if du < 0.0:
		return
	var ou := maxf(progress("door_open"), 0.0)
	var wu := maxf(progress("walk_in"), 0.0)
	var we: float = smooth.call(wu)
	var door := assets.interlude_sprite("cell_door_frame")
	if door.is_empty() or door["tex"] == null:
		door = assets.interlude_sprite("cell_door")
	if door.is_empty() or door["tex"] == null:
		return
	var px: float = door["scale"]  # design px per texture px
	var op: Array = assets.interlude_anchor("door_opening", [546, 62, 188, 378])
	var dc: Array = assets.interlude_anchor("door_centre", [640, 440])
	var o_pos := Vector2(float(op[0]) - float(dc[0]) + 160.0, float(op[1]) - float(dc[1]) + 440.0)  # the opening, in the door's own design px
	var o_size := Vector2(float(op[2]), float(op[3]))
	var piv := Vector2(160.0, 440.0)  # the door's foot in its own design px (pivot bottom centre)
	var k0 := clampf(view.size.y * 0.78 / 440.0, 0.5, 2.0)  # the door at rest: about three quarters of the screen tall
	var k: float = k0 * lerpf(1.0, 6.4, we * we)
	var c0 := Vector2(vc.x, view.position.y + view.size.y * 0.5 + 18.0)
	var oc: Vector2 = c0.lerp(vc, we)  # the opening's centre: where we are walking to
	var foot := oc - (o_pos + o_size * 0.5 - piv) * k
	var o_rect := Rect2(foot + (o_pos - piv) * k, o_size * k)
	var fade_in: float = smooth.call(clampf(du, 0.0, 1.0))
	# the day room beyond the door (the new chapter's own backdrop), seen through the opening, growing to fill the screen
	var bl := assets.layer("backdrop")
	var btex: Texture2D = assets.texture(str(bl.get("file", ""))) if not bl.is_empty() else null
	if btex != null and ou > 0.0:
		var lpos := Vector2(float(bl["pos"][0]), float(bl["pos"][1]))
		var lsize := Vector2(float(bl["size"][0]), float(bl["size"][1]))
		var full := Rect2(view.position, view.size)  # the 1280 x 720 frame of the day room maps onto the visible screen at the end
		var start := Rect2(oc - view.size * 0.31, view.size * 0.62)
		var room := Rect2(start.position.lerp(full.position, we), start.size.lerp(full.size, we))
		var sc := Vector2(1280.0, 720.0) / room.size  # design px of the room per screen px
		var lit: float = smooth.call(clampf(ou * 1.6, 0.0, 1.0))
		var shown := o_rect.intersection(view.grow(4.0))
		if shown.size.x > 1.0 and shown.size.y > 1.0:
			var d0 := (shown.position - room.position) * sc - lpos
			var src := Rect2(d0 * Vector2(btex.get_width(), btex.get_height()) / lsize, shown.size * sc * Vector2(btex.get_width(), btex.get_height()) / lsize)
			draw_texture_rect_region(btex, shown, src, Color(1, 1, 1, lit * fade_in))
			draw_rect(shown, Color(1.0, 0.86, 0.62, 0.22 * lit * (1.0 - we)))  # warm light spilling out of the room
	# the ward wall the door is set in (mint, with a lilac dado and skirting) and the floor it stands on, around the frame's footprint
	var fr := Rect2(foot + (Vector2(40.0, 36.0) - piv) * k, Vector2(240.0, 404.0) * k)  # the painted frame inside the 320 x 440 sprite
	var big := view.grow(16.0)
	var wall := Color(0.78, 0.92, 0.87, fade_in)
	var dado_top := foot.y - 96.0 * k
	for r in [Rect2(big.position.x, big.position.y, big.size.x, fr.position.y - big.position.y),
			Rect2(big.position.x, fr.position.y, fr.position.x - big.position.x, foot.y - fr.position.y),
			Rect2(fr.end.x, fr.position.y, big.end.x - fr.end.x, foot.y - fr.position.y)]:
		if r.size.x <= 0.0 or r.size.y <= 0.0:
			continue
		draw_rect(r, wall)
		var dr: Rect2 = (r as Rect2).intersection(Rect2(big.position.x, dado_top, big.size.x, foot.y - dado_top))
		if dr.size.y > 0.0 and dr.size.x > 0.0:
			draw_rect(dr, Color(0.76, 0.71, 0.92, fade_in))
			draw_rect(Rect2(dr.position.x, dr.position.y - 3.0 * k, dr.size.x, 5.0 * k), Color(0.9, 0.87, 0.98, fade_in))
			draw_rect(Rect2(dr.position.x, foot.y - 9.0 * k, dr.size.x, 9.0 * k), Color(0.55, 0.49, 0.74, fade_in))
	var star_cols := [Color(1.0, 0.85, 0.4), Color(1.0, 0.56, 0.54), Color(0.56, 0.85, 0.78), Color(0.73, 0.65, 0.94)]
	for i in 6:  # paper stars stuck on the wall either side of the door
		var sp := foot + Vector2((-1.0 if i % 2 == 0 else 1.0) * (190.0 + 40.0 * float(i / 2)), -330.0 + 90.0 * float(i / 2) - 20.0 * float(i % 2)) * k
		var pts := PackedVector2Array()
		for j in 10:
			var ang := -PI * 0.5 + float(j) * PI / 5.0 + 0.2 * float(i)
			pts.append(sp + Vector2.from_angle(ang) * (13.0 if j % 2 == 0 else 5.6) * k)
		draw_colored_polygon(pts, Color(star_cols[i % 4], fade_in))
		pts.append(pts[0])
		draw_polyline(pts, Color(0.11, 0.06, 0.25, fade_in), maxf(1.5 * k, 1.0))
	if foot.y < big.end.y:
		draw_rect(Rect2(big.position.x, foot.y, big.size.x, big.end.y - foot.y), Color(0.74, 0.84, 0.82, fade_in))
		draw_rect(Rect2(big.position.x, foot.y, big.size.x, 4.0 * k), Color(0.3, 0.25, 0.45, 0.35 * fade_in))
		draw_rect(Rect2(fr.position.x - 20.0 * k, foot.y, fr.size.x + 40.0 * k, 14.0 * k), Color(1.0, 0.86, 0.62, 0.25 * fade_in * smooth.call(clampf(ou * 1.6, 0.0, 1.0))))
	# the frame and the leaf
	draw_set_transform(foot, 0.0, Vector2(k, k) * px)
	draw_texture(door["tex"], -piv / px, Color(1, 1, 1, fade_in))
	draw_set_transform_matrix(Transform2D.IDENTITY)
	var leaf := assets.interlude_sprite("cell_door_leaf")
	var leaf_open := assets.interlude_sprite("cell_door_open")
	var hinge := foot + (Vector2(o_pos.x, o_pos.y + o_size.y) - piv) * k
	var swing: float = smooth.call(clampf(ou, 0.0, 1.0))
	if not leaf.is_empty() and leaf["tex"] != null and swing < 0.82:
		var sx := lerpf(1.0, 0.18, swing / 0.82)
		var shade := 1.0 - 0.3 * swing
		draw_set_transform(hinge, 0.0, Vector2(k * sx, k) * float(leaf["scale"]))
		draw_texture(leaf["tex"], -leaf["pivot"], Color(shade, shade, shade * 1.02, fade_in * clampf((0.82 - swing) / 0.12, 0.0, 1.0)))
		draw_set_transform_matrix(Transform2D.IDENTITY)
	if not leaf_open.is_empty() and leaf_open["tex"] != null and swing > 0.6:
		draw_set_transform(hinge, 0.0, Vector2(k, k) * float(leaf_open["scale"]))
		draw_texture(leaf_open["tex"], -leaf_open["pivot"], Color(0.9, 0.9, 0.92, fade_in * clampf((swing - 0.6) / 0.25, 0.0, 1.0)))
		draw_set_transform_matrix(Transform2D.IDENTITY)
	var wh := progress("white")
	if wh >= 0.0:
		draw_rect(view.grow(12.0), Color(0.97, 1.0, 0.98, smooth.call(wh)))
