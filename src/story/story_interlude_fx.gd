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


## Waking in a hospital bed: the room goes dark behind closed eyelids, a heartbeat trace and a beep, then the lids open onto warm light.
func _draw_awakening() -> void:
	var cl := progress("eyelids_close")
	var op := progress("eyelids_open")
	var closed := 0.0
	if cl >= 0.0:
		closed = cl * cl * (3.0 - 2.0 * cl)
	if op >= 0.0:
		closed = 1.0 - op * op * (3.0 - 2.0 * op)
	if closed > 0.001:
		var edge := closed * 372.0  # each lid covers this much from its side; they meet in the middle when closed
		var top := assets.interlude_sprite("eyelid_top")
		var bot := assets.interlude_sprite("eyelid_bottom")
		draw_rect(Rect2(-10, -10, 1300, edge + 10), Color(0.12, 0.05, 0.07))
		draw_rect(Rect2(-10, 720 - edge, 1300, edge + 10), Color(0.12, 0.05, 0.07))
		if not top.is_empty() and top["tex"] != null:
			var h := float(top["tex"].get_height()) * float(top["scale"])
			draw_texture_rect(top["tex"], Rect2(-10, edge - h, 1300, h), false, Color(1, 1, 1, 1))
		if not bot.is_empty() and bot["tex"] != null:
			var h2 := float(bot["tex"].get_height()) * float(bot["scale"])
			draw_texture_rect(bot["tex"], Rect2(-10, 720 - edge, 1300, h2), false, Color(1, 1, 1, 1))
	var mu := progress("monitor")
	if mu >= 0.0 and t < float(ev("monitor")["t"]) + float(ev("monitor")["dur"]):
		var ml := assets.interlude_sprite("monitor_line")
		var beat := fposmod(t * 1.1, 1.0)
		var glow := exp(-beat * 6.0)
		if not ml.is_empty() and ml["tex"] != null:
			var w := float(ml["tex"].get_width()) * float(ml["scale"])
			var x := fposmod(t * 160.0, maxf(w, 1.0))
			var fade := clampf(mu * 4.0, 0.0, 1.0) * (1.0 - clampf((closed - 0.9) * 10.0, 0.0, 1.0) * 0.0)
			for k in range(-1, int(1300.0 / maxf(w, 1.0)) + 2):
				_spr("monitor_line", Vector2(float(k) * w - x, 340.0), Vector2.ONE, 0.0, Color(0.5, 1.0, 0.7, 0.55 * fade + 0.4 * glow * fade))
		draw_circle(Vector2(640, 340), 4.0 + 14.0 * glow, Color(0.5, 1.0, 0.7, 0.25 * glow))
	var wu := progress("white")
	if wu >= 0.0:
		_full(Color(1.0, 0.97, 0.9, clampf(wu * 1.3, 0.0, 1.0)))
	elif op >= 0.0:
		_full(Color(1.0, 0.97, 0.9, 0.5 * (1.0 - closed) * op))


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
