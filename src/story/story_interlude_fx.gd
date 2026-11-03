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
	if kind == "abduction":
		_draw_abduction()
	else:
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
