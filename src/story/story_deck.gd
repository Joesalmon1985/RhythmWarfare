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


## 0 (dancer's floor-tile rail) .. 1 (DJ deck) at song time `now`; a chapter without a journey always shows the deck.
func deck_mix(now: float) -> float:
	return stage.player.deck_mix_at(now) if stage != null and stage.player != null else 1.0


## A node that draws once through a callable (CanvasItem draw commands are kept until it is asked to redraw): the deck's static layers cost nothing per frame.
class _Painter extends Node2D:
	var fn := Callable()

	func _draw() -> void:
		if fn.is_valid():
			fn.call(self)


var _layer: Node2D  # behind the pad view: desk top, the platters (rotated, not redrawn), the bank plates, bezels and lip glow
var _layer_key := ""
var _platters: Array = []  # {node, centre}


func _sync_layer(ci: CanvasItem, size: Vector2, rects: Dictionary, mix: float, now: float) -> void:
	var key := "%s|%s" % [size, str(rects)]
	if _layer == null or not is_instance_valid(_layer) or key != _layer_key:
		if _layer != null and is_instance_valid(_layer):
			_layer.queue_free()
		_layer_key = key
		_layer = Node2D.new()
		_layer.name = "DeckLayer"
		_layer.show_behind_parent = true
		ci.add_child(_layer)
		_platters = []
		var bottom := _Painter.new()
		bottom.fn = func(c: CanvasItem) -> void: _draw_desk_top(c, size)
		_layer.add_child(bottom)
		var r1: Rect2 = rects[1]
		var r2: Rect2 = rects[2]
		var r3: Rect2 = rects[3]
		var r4: Rect2 = rects[4]
		for pair in [[r1, r2], [r3, r4]]:
			var a: Rect2 = pair[0]
			var c2: Rect2 = pair[1]
			var rad := a.size.x * 1.13
			var pn := _Painter.new()
			pn.position = Vector2((a.position.x + c2.end.x) * 0.5, (a.position.y + a.end.y) * 0.5)
			pn.fn = func(c: CanvasItem) -> void: _spr(c, "platter", Vector2.ZERO, Vector2(rad * 2.0, rad * 2.0), Color(1, 1, 1, 0.9), 0.0)
			_layer.add_child(pn)
			_platters.append(pn)
		var top := _Painter.new()
		top.fn = func(c: CanvasItem) -> void: _draw_desk_plates(c, size, rects)
		_layer.add_child(top)
	_layer.visible = mix > 0.01
	_layer.modulate.a = mix
	var rot := _beats(now) * 0.35
	for pn in _platters:
		(pn as Node2D).rotation = rot


func draw_under(ci: CanvasItem, size: Vector2, rects: Dictionary, now: float) -> void:
	var m := deck_mix(now)
	_sync_layer(ci, size, rects, m, now)
	if m > 0.01:
		_draw_deck(ci, size, rects, now)
	if m < 0.99:
		_draw_dancer_rail(ci, size, rects, now, 1.0 if m <= 0.01 else 1.0 - m)


## The dancer's strip: a dark floor with a rail of four lit LED floor tiles, one under each pad, in the colours of the club's dance floor.
func _draw_dancer_rail(ci: CanvasItem, size: Vector2, rects: Dictionary, now: float, alpha: float) -> void:
	ci.draw_rect(Rect2(Vector2.ZERO, size), Color(0.025, 0.018, 0.07, alpha))
	var tex := assets.texture("textures/floor_led.png")
	var b := _beats(now)
	var kp := exp(-6.0 * (b - floor(b)))
	for pad in rects:
		var r: Rect2 = rects[pad]
		var tile := r.grow(r.size.x * 0.1)
		if tex != null:  # a different cell of the floor texture under each pad
			var q := int(pad) % 4
			var src := Rect2(float(q % 2) * 64.0, float(q / 2) * 64.0, 64.0, 64.0)
			ci.draw_texture_rect_region(tex, tile, src, Color(1, 1, 1, alpha))
		else:
			ci.draw_rect(tile, Color(0.2, 0.15, 0.5, alpha))
		var edge := Color(0.5, 0.6, 1.0, (0.35 + 0.35 * kp * (0.3 if reduced else 1.0)) * alpha)
		ci.draw_rect(tile, edge, false, 3.0)
	var ry := size.y * 0.06  # the rail: a neon line along the top of the strip and along its foot
	ci.draw_rect(Rect2(0, ry, size.x, 3.0), Color(1.0, 0.35, 0.78, 0.6 * alpha))
	ci.draw_rect(Rect2(0, size.y - 6.0, size.x, 3.0), Color(0.35, 0.92, 1.0, 0.5 * alpha))


func _draw_desk_top(ci: CanvasItem, size: Vector2) -> void:
	var layer := assets.layer("desk_top")
	var tex := assets.texture(str(layer.get("file", "")))
	if tex != null:
		ci.draw_texture_rect(tex, Rect2(Vector2.ZERO, size), false)
	else:
		ci.draw_rect(Rect2(Vector2.ZERO, size), Color(0.05, 0.06, 0.1, 1.0))


func _draw_desk_plates(ci: CanvasItem, size: Vector2, rects: Dictionary) -> void:
	for pair in [[rects[1], rects[2]], [rects[3], rects[4]]]:  # each pad pair sits on one bank plate over the platter's centre
		var bank := (pair[0] as Rect2).merge(pair[1]).grow((pair[0] as Rect2).size.x * 0.11)
		_plate(ci, bank)
	for pad in rects:
		var rb: Rect2 = rects[pad]
		var gb := rb.size.x * 0.1
		_spr(ci, "pad_bezel", rb.position - Vector2(gb, gb), rb.size + Vector2(gb, gb) * 2.0)
	_spr(ci, "desk_lip_glow", Vector2(0, 0), Vector2(size.x, size.y * 0.06), Color(1, 1, 1, 0.9))


## The moving parts of the desk, drawn every frame: knobs, crossfader, VU meters (everything else is the static layer behind the pads).
func _draw_deck(ci: CanvasItem, size: Vector2, rects: Dictionary, now: float) -> void:
	var b := _beats(now)
	var r2: Rect2 = rects[2]
	var r3: Rect2 = rects[3]
	var x0 := r2.end.x + 22.0
	var x1 := r3.position.x - 22.0
	var w := x1 - x0
	if w > 120.0:
		var n := 6
		for i in n:
			var kx := x0 + w * (float(i) + 0.5) / float(n)
			var ks := minf(w / float(n) * 0.55, size.y * 0.1)
			_spr(ci, "knob", Vector2(kx, size.y * 0.075), Vector2(ks, ks), Color.WHITE, -1.2 + 2.4 * (0.5 + 0.5 * sin(b * 0.07 * float(i + 1) + float(i))))
		var slot_w := minf(w * 0.7, 240.0)
		var cy := size.y * 0.965
		_spr(ci, "fader_slot", Vector2(x0 + w * 0.5, cy), Vector2(slot_w, size.y * 0.05))
		var cap_x := x0 + w * 0.5 + sin(b * 0.12) * slot_w * 0.4
		_spr(ci, "fader_cap", Vector2(cap_x, cy), Vector2(size.y * 0.075, size.y * 0.075))
		_draw_vu(ci, Vector2(r2.end.x + r2.size.x * 0.11 + 6.0, r2.position.y + r2.size.y * 0.1), size.y * 0.5, now)
		_draw_vu(ci, Vector2(r3.position.x - r3.size.x * 0.11 - 16.0, r3.position.y + r3.size.y * 0.1), size.y * 0.5, now)


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
