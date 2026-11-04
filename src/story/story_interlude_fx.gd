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


## Coming to on a ward: plain cold light, a slow-breathing tunnel, then a ward door swings open onto the new room.
func _draw_sectioned() -> void:
	var fu := progress("fluoro")
	if fu >= 0.0:
		var ws := assets.interlude_sprite("fluoro_wash")
		var a := clampf(fu * 1.3, 0.0, 0.85)
		if not ws.is_empty() and ws["tex"] != null:
			draw_texture_rect(ws["tex"], Rect2(-10, -10, 1300, 740), false, Color(1, 1, 1, a))
		else:
			_full(Color(0.8, 1.0, 0.95, a * 0.6))
		for i in 4:  # slow, soft tube flicker (never a strobe)
			var flick := 0.75 + 0.25 * sin(t * (1.3 + 0.4 * float(i)) + float(i) * 2.0)
			_spr("flicker_tube", Vector2(200.0 + float(i) * 280.0, 40.0), Vector2.ONE, 0.0, Color(1, 1, 1, flick * clampf(fu * 2.0, 0.0, 1.0)))
	var tu := progress("tunnel")
	if tu >= 0.0:
		var tv := assets.interlude_sprite("tunnel_vignette")
		var breathe := 1.0 + 0.04 * sin(t * 1.6)
		if not tv.is_empty() and tv["tex"] != null:
			draw_texture_rect(tv["tex"], Rect2(640.0 - 760.0 * breathe, 360.0 - 430.0 * breathe, 1520.0 * breathe, 860.0 * breathe), false, Color(1, 1, 1, clampf(tu * 1.5, 0.0, 0.9)))
		else:
			_full(Color(0.0, 0.05, 0.05, 0.4 * tu))
	var du := progress("door")
	if du >= 0.0:
		var e := du * du * (3.0 - 2.0 * du)
		_full(Color(0.95, 1.0, 0.97, clampf(du * 1.6, 0.0, 0.9)))
		_spr("cell_door", Vector2(640, 360), Vector2.ONE * lerpf(0.5, 3.0, e), 0.0, Color(1, 1, 1, clampf(1.0 - (du - 0.7) / 0.3, 0.0, 1.0)))
	var wu := progress("white")
	if wu >= 0.0:
		_full(Color(0.96, 1.0, 0.98, clampf(wu * 1.3, 0.0, 1.0)))
