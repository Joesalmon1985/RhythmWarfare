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
