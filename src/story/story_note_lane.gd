class_name StoryNoteLane
extends NoteLane
## The Story Campaign's skin of the falling notes: the same NoteLane (same visible_notes / shape_rect geometry, so every note lands
## exactly on its pad at its hit time) drawn as backlit glass tiles that read over the lit club: a dark tinted body (contrast against
## bright beams), a glowing rim in the pad family's colour, the family's shape engraved in the middle and, for a hold, a lit core
## running the length of the bar. A tile is drawn a little narrower than its rectangle and its head is centred on the rectangle's
## centre, so it covers less of the crowd while still crossing the pad's centre exactly on the beat.

const INSET_X := 0.08  # each side, share of the pad width
const HEAD_H := 0.56  # tap tile height, share of the pad height (centred)

var glow_tex: Texture2D


func _draw() -> void:
	if level == null or clock == null or pad_view == null:
		return
	var palette: Dictionary = PadView.HC_COLOR if high_contrast else PadView.FAMILY_COLOR
	for v in visible_notes(clock.judge_time()):
		var n: Dictionary = level.notes[int(v["index"])]
		var r: Rect2 = v["rect"]
		var col: Color = palette.get(str(n.get("family", n.get("lane", ""))), Color(0.7, 0.72, 0.76))
		var fam := str(n.get("family", n.get("lane", "")))
		var fade := 1.0
		var miss: bool = v["state"] == "miss"
		if miss:
			col = col.lerp(MISS_TINT, 0.7)
			if not reduced_effects and float(v["end_dt"]) < 0.0:
				fade = clampf(1.0 + float(v["end_dt"]) / VISIBLE_AFTER_S, 0.0, 1.0)
		var s := r.size.x
		var pad_h := s  # the pad is square; a hold's rect is the pad plus its length above
		var head_h := pad_h * HEAD_H
		var x := r.position.x + s * INSET_X
		var w := s * (1.0 - 2.0 * INSET_X)
		var head := Rect2(x, r.end.y - pad_h * 0.5 - head_h * 0.5, w, head_h)
		var tile := head
		if v["hold"]:
			tile = Rect2(x + w * 0.18, r.position.y + pad_h * (0.5 - HEAD_H * 0.5), w * 0.64, head.end.y - (r.position.y + pad_h * (0.5 - HEAD_H * 0.5)))
		var near := clampf(1.0 - float(v["dt"]) / 0.35, 0.0, 1.0) if float(v["dt"]) > 0.0 else 1.0
		if v["hold"]:
			_tile(tile, col, fade, near * 0.6, s * 0.08, false)
		_tile(head, col, fade, near, s * 0.12, true)
		_icon(fam, head, col, fade)
	if pad_view is StoryPadView:
		(pad_view as StoryPadView).draw_feedback_layer(self, _pad_rects_local())


func _tile(r: Rect2, col: Color, fade: float, near: float, radius: float, is_head: bool) -> void:
	var hc := high_contrast
	if glow_tex != null and not reduced_effects:  # the soft halo that separates the tile from the busy scene behind it
		draw_texture_rect(glow_tex, r.grow(r.size.x * 0.22), false, Color(col, (0.16 + 0.22 * near) * fade))
	var body := Color(col.darkened(0.55), (0.9 if hc else 0.74) * fade)
	_round_rect(r, body, radius)
	# a lighter inner face (backlit glass), brighter at the top edge
	_round_rect(r.grow(-r.size.x * 0.07), Color(col.darkened(0.15), (0.55 if hc else 0.38 + 0.25 * near) * fade), radius * 0.7)
	_round_rect(Rect2(r.position + Vector2(r.size.x * 0.1, r.size.y * 0.06), Vector2(r.size.x * 0.8, minf(r.size.y * 0.18, 18.0))), Color(1, 1, 1, 0.16 * fade), radius * 0.5)
	_round_outline(r, Color(col.lightened(0.45), (0.95 if is_head else 0.75) * fade), radius, 4.0 if hc else 3.0)
	if hc:
		_round_outline(r.grow(2.0), Color(1, 1, 1, 0.9 * fade), radius + 2.0, 2.0)


func _icon(fam: String, r: Rect2, col: Color, fade: float) -> void:
	var c := r.get_center()
	var s := minf(r.size.x, r.size.y) * 0.2
	var ic := Color(col.lightened(0.7), 0.95 * fade)
	match fam:
		"kick":
			draw_circle(c, s, ic)
		"snare":
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -s * 1.2), c + Vector2(s * 1.2, 0), c + Vector2(0, s * 1.2), c + Vector2(-s * 1.2, 0)]), ic)
		"bass":
			for k in 3:
				var w := s * (2.2 - 0.5 * absf(k - 1))
				draw_rect(Rect2(c.x - w * 0.5, c.y - s + k * s * 0.8, w, s * 0.42), ic)
