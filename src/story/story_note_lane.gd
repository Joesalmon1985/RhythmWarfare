class_name StoryNoteLane
extends NoteLane
## The Story Campaign's skin of the falling notes, drawn as light over the picture (lead ruling 29, style guide section 11): the same
## NoteLane (same visible_notes / shape_rect geometry, so every note lands exactly on its pad at its hit time; nothing here moves a note
## in time or space) drawn as
##   * a tap: the tile's outline lit in the pad family's colour round a faint body (at most a third opaque), a bright leading edge along
##     its bottom (the edge that meets the pad), the family's shape in the middle (disc, diamond, bars: the families differ by shape and by
##     lane, not by hue alone), and a thin dark line outside the light so it reads over a white sky as well as over a dark room;
##   * a hold: the same head, a lit core one third of the pad wide running up to the hold's end, and an end bar that crosses the pad's
##     centre at the release time. While the pad is held the head stays on the pad and the core drains into it.
## The tile is a little narrower than its rectangle and its head is centred on the rectangle's square, so it crosses the pad's centre
## exactly on the beat.

const INSET_X := 0.08  # each side, share of the pad width
const HEAD_H := 0.56  # tap tile height, share of the pad height (centred)
const CORE_W := 1.0 / 3.0  # a hold's core: share of the pad width
const BODY_A := 0.14  # a tile's body over the picture (style guide: at most 0.35)
const INK := Color(0.075, 0.067, 0.122)  # #13111f, the shared shadow ink
const RADIUS := 10.0  # the UI's one corner radius

var glow_tex: Texture2D
static var draw_usec := 0  # CPU time spent recording this layer's draw commands (tools/art/a3_drawcost.gd reads it)


func _draw() -> void:
	var t0 := Time.get_ticks_usec()
	_draw_notes()
	draw_usec += Time.get_ticks_usec() - t0


func _draw_notes() -> void:
	if level == null or clock == null or pad_view == null:
		return
	if glow_tex == null:
		glow_tex = StoryPadView.soft_glow()
	var palette: Dictionary = PadView.HC_COLOR if high_contrast else PadView.FAMILY_COLOR
	var now := clock.judge_time()
	var pads := _pad_rects_local()
	for v in visible_notes(now, pads):
		var n: Dictionary = level.notes[int(v["index"])]
		var r: Rect2 = v["rect"]
		var fam := str(n.get("family", n.get("lane", "")))
		var col: Color = palette.get(fam, Color(0.7, 0.72, 0.76))
		var fade := 1.0
		var miss: bool = v["state"] == "miss"
		if miss:
			col = col.lerp(MISS_TINT, 0.7)
			if not reduced_effects and float(v["end_dt"]) < 0.0:
				fade = clampf(1.0 + float(v["end_dt"]) / VISIBLE_AFTER_S, 0.0, 1.0)
		var s := r.size.x  # the pad is square; a hold's rect is the pad plus its length above
		var head_h := s * HEAD_H
		var x := r.position.x + s * INSET_X
		var w := s * (1.0 - 2.0 * INSET_X)
		var head_c := r.end.y - s * 0.5
		var near := clampf(1.0 - float(v["dt"]) / 0.35, 0.0, 1.0) if float(v["dt"]) > 0.0 else 1.0
		if v["hold"]:
			var pad_c: float = (pads[int(v["pad"])] as Rect2).get_center().y
			var held := not miss and float(v["dt"]) <= 0.0 and pad_view.holding_fn.is_valid() and float(pad_view.holding_fn.call(int(v["pad"]), now)) >= 0.0
			if held:
				head_c = minf(head_c, pad_c)
			var tail_c := r.position.y + s * 0.5
			_core(r.get_center().x, tail_c, head_c, w, s, col, fade, near)
		var head := Rect2(x, head_c - head_h * 0.5, w, head_h)
		_tile(head, col, fade, near)
		_icon(fam, head, col, fade)
	if pad_view is StoryPadView:
		(pad_view as StoryPadView).draw_feedback_layer(self, pads)


## A note's head drawn as light: a soft halo, a faint body, the dark line outside, the lit outline, a hot inner line, the bright leading edge.
func _tile(r: Rect2, col: Color, fade: float, near: float) -> void:
	var hc := high_contrast
	var lit := col.lightened(0.35)
	if glow_tex != null:
		draw_texture_rect(glow_tex, r.grow(r.size.x * 0.2), false, Color(col, (0.10 + 0.16 * near) * fade))
	_round_rect(r, Color(col, ((0.32 if hc else BODY_A) + 0.06 * near) * fade), RADIUS)
	_round_outline(r.grow(2.0), Color(INK, (0.85 if hc else 0.6) * fade), RADIUS + 2.0, 3.0 if hc else 2.0)
	_round_outline(r, Color(lit, 0.95 * fade), RADIUS, 4.0 if hc else 3.0)
	_round_outline(r.grow(-3.0), Color(col.lightened(0.75), (0.25 + 0.2 * near) * fade), RADIUS - 3.0, 1.0)
	var edge := Rect2(r.position.x + RADIUS * 0.6, r.end.y - 5.0, r.size.x - RADIUS * 1.2, 4.0)
	draw_rect(edge.grow(1.0), Color(INK, 0.6 * fade))
	draw_rect(edge, Color(col.lightened(0.8), fade))
	if hc:
		_round_outline(r.grow(4.0), Color(1, 1, 1, 0.9 * fade), RADIUS + 4.0, 2.0)


## A hold's body: a lit core from its head up to its end bar (y grows downwards: tail_c above head_c).
func _core(cx: float, tail_c: float, head_c: float, w: float, s: float, col: Color, fade: float, near: float) -> void:
	if tail_c >= head_c - 1.0:
		return
	var cw := s * CORE_W
	var span := head_c - tail_c
	draw_rect(Rect2(cx - cw * 0.5, tail_c, cw, span), Color(col, ((0.24 if high_contrast else 0.12) + 0.04 * near) * fade))
	draw_rect(Rect2(cx - 4.0, tail_c, 8.0, span), Color(INK, 0.55 * fade))
	draw_rect(Rect2(cx - 3.0, tail_c, 6.0, span), Color(col.lightened(0.3), 0.9 * fade))
	draw_rect(Rect2(cx - 1.0, tail_c, 2.0, span), Color(col.lightened(0.8), 0.9 * fade))
	var cap := Rect2(cx - w * 0.34, tail_c - 4.0, w * 0.68, 8.0)  # the end bar: crosses the pad's centre at the release time
	_round_rect(cap.grow(2.0), Color(INK, 0.7 * fade), 5.0)
	_round_rect(cap, Color(col.lightened(0.45), 0.95 * fade), 4.0)
	draw_rect(Rect2(cap.position.x + 3.0, cap.position.y + 2.0, cap.size.x - 6.0, 2.0), Color(1, 1, 1, 0.5 * fade))


func _icon(fam: String, r: Rect2, col: Color, fade: float) -> void:
	var c := r.get_center()
	var s := minf(r.size.x, r.size.y) * 0.2
	var ic := Color(col.lightened(0.7), 0.95 * fade)
	var ink := Color(INK, 0.7 * fade)
	match fam:
		"kick":
			draw_circle(c, s + 2.0, ink)
			draw_circle(c, s, ic)
		"snare":
			var k := s * 1.2
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -k - 2.8), c + Vector2(k + 2.8, 0), c + Vector2(0, k + 2.8), c + Vector2(-k - 2.8, 0)]), ink)
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -k), c + Vector2(k, 0), c + Vector2(0, k), c + Vector2(-k, 0)]), ic)
		"bass":
			for k in 3:
				var bw := s * (2.2 - 0.5 * absf(k - 1))
				draw_rect(Rect2(c.x - bw * 0.5, c.y - s + k * s * 0.8, bw, s * 0.42).grow(1.5), ink)
			for k in 3:
				var bw := s * (2.2 - 0.5 * absf(k - 1))
				draw_rect(Rect2(c.x - bw * 0.5, c.y - s + k * s * 0.8, bw, s * 0.42), ic)
