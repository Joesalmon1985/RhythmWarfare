class_name StoryDeck
extends RefCounted
## The DJ deck skin for the pad strip: PadView stays the only input (its pads, hit rectangles and falling-note landing zones are
## unchanged); this draws the mixing desk around and under them (desk top, platters, bezels, knobs, VU meters, crossfader, lip glow)
## from the art manifest, animated from the song clock. Hooks: PadView.deck_under / deck_over.

var assets: StoryAssets
var run: StoryRun
var stage: StoryStage
var reduced := false
var high_contrast := false


func setup(p_assets: StoryAssets, p_run: StoryRun, p_stage: StoryStage) -> void:
	assets = p_assets
	run = p_run
	stage = p_stage


func _spr(ci: CanvasItem, id: String, pos: Vector2, size: Vector2, col := Color.WHITE, rot := 0.0) -> void:
	var s: Dictionary = assets.sprite(id)
	if s.is_empty() or s["tex"] == null:
		return
	var tex: Texture2D = s["tex"]
	var k: float = s["scale"]
	ci.draw_set_transform(pos, rot, Vector2(size.x / (float(tex.get_width()) * k), size.y / (float(tex.get_height()) * k)) * k)
	ci.draw_texture(tex, -s["pivot"], col)
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


func _beats(now: float) -> float:
	return maxf(now, 0.0) * run.level.bpm / 60.0


func draw_under(ci: CanvasItem, size: Vector2, rects: Dictionary, now: float) -> void:
	var layer := assets.layer("desk_top")
	var tex := assets.texture(str(layer.get("file", "")))
	if tex != null:
		ci.draw_texture_rect(tex, Rect2(Vector2.ZERO, size), false)
	else:
		ci.draw_rect(Rect2(Vector2.ZERO, size), Color(0.05, 0.06, 0.1, 1.0))
	var b := _beats(now)
	var r1: Rect2 = rects[1]
	var r2: Rect2 = rects[2]
	var r3: Rect2 = rects[3]
	var r4: Rect2 = rects[4]
	for pair in [[r1, r2], [r3, r4]]:
		var a: Rect2 = pair[0]
		var c: Rect2 = pair[1]
		var centre := Vector2((a.position.x + c.end.x) * 0.5, (a.position.y + a.end.y) * 0.5)
		var rad := a.size.x * 1.13
		_spr(ci, "platter", centre, Vector2(rad * 2.0, rad * 2.0), Color(1, 1, 1, 0.9), b * 0.35)
	for pair in [[r1, r2], [r3, r4]]:  # each pad pair sits on one bank plate over the platter's centre
		var bank := (pair[0] as Rect2).merge(pair[1]).grow((pair[0] as Rect2).size.x * 0.11)
		_plate(ci, bank)
	for pad in rects:
		var rb: Rect2 = rects[pad]
		var gb := rb.size.x * 0.1
		_spr(ci, "pad_bezel", rb.position - Vector2(gb, gb), rb.size + Vector2(gb, gb) * 2.0)
	# knob row along the top of the centre column
	var x0 := r2.end.x + 22.0
	var x1 := r3.position.x - 22.0
	var w := x1 - x0
	if w > 120.0:
		var n := 6
		for i in n:
			var kx := x0 + w * (float(i) + 0.5) / float(n)
			var ks := minf(w / float(n) * 0.55, size.y * 0.1)
			_spr(ci, "knob", Vector2(kx, size.y * 0.075), Vector2(ks, ks), Color.WHITE, -1.2 + 2.4 * (0.5 + 0.5 * sin(b * 0.07 * float(i + 1) + float(i))))
		# crossfader slot and cap at the foot of the centre column
		var slot_w := minf(w * 0.7, 240.0)
		var cy := size.y * 0.965
		_spr(ci, "fader_slot", Vector2(x0 + w * 0.5, cy), Vector2(slot_w, size.y * 0.05))
		var cap_x := x0 + w * 0.5 + sin(b * 0.12) * slot_w * 0.4
		_spr(ci, "fader_cap", Vector2(cap_x, cy), Vector2(size.y * 0.075, size.y * 0.075))
		_draw_vu(ci, Vector2(r2.end.x + r2.size.x * 0.11 + 6.0, r2.position.y + r2.size.y * 0.1), size.y * 0.5, now)
		_draw_vu(ci, Vector2(r3.position.x - r3.size.x * 0.11 - 16.0, r3.position.y + r3.size.y * 0.1), size.y * 0.5, now)
	_spr(ci, "desk_lip_glow", Vector2(0, 0), Vector2(size.x, size.y * 0.06), Color(1, 1, 1, 0.9))


var _plate_box := StyleBoxFlat.new()


func _plate(ci: CanvasItem, r: Rect2) -> void:
	_plate_box.bg_color = Color(0.035, 0.025, 0.09, 0.96)
	_plate_box.border_color = Color(0.42, 0.32, 0.85, 0.55)
	_plate_box.set_border_width_all(2)
	_plate_box.set_corner_radius_all(int(r.size.y * 0.1))
	_plate_box.shadow_color = Color(0, 0, 0, 0.5)
	_plate_box.shadow_size = 8
	_plate_box.shadow_offset = Vector2(0, 3)
	ci.draw_style_box(_plate_box, r)


func _draw_vu(ci: CanvasItem, at: Vector2, h: float, now: float) -> void:
	var e := clampf(run.crowd.energy / 100.0, 0.0, 1.0)
	var b := _beats(now)
	var segs := 10
	var kp := exp(-6.0 * (b - floor(b)))  # peaks on every beat, decays before the next one
	var wob := 0.5 + 0.5 * sin(b * PI * 0.5 + at.x * 0.013)
	var lit := int(clampf((0.2 + 0.8 * e) * (0.45 + 0.4 * kp + 0.15 * wob) * float(segs) + 0.5, 0.0, float(segs)))
	var sh := h / float(segs)
	for i in segs:
		var on := i < lit
		var col := Color(0.2, 0.9, 0.6) if i < 6 else (Color(1.0, 0.8, 0.25) if i < 8 else Color(1.0, 0.35, 0.4))
		var rr := Rect2(at.x, at.y + h - float(i + 1) * sh + 1.0, 10.0, sh - 2.0)
		ci.draw_rect(rr, Color(col, 0.95 if on else 0.14))


func draw_over(_ci: CanvasItem, _size: Vector2, _rects: Dictionary, _now: float) -> void:
	pass  # the skinned pads (StoryPadView) light themselves
