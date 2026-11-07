class_name StoryPadView
extends PadView
## The Story Campaign's skin of the four pads: the same PadView (hit rectangles, touch rectangles, pulses, hold fill, labels, keys and
## feedback all come from the base class and keep their meaning), drawn as backlit rubber pads set into the world's board (StoryDeck:
## an unlit pad, its rim and the display take the board's colours; a lit pad keeps its family colour, the game's colour code). Adds the
## board's display (the sequence meter, the mode banner and a crowd-energy meter) and the hit/miss juice: a ring burst and a word on a
## hit, a red flinch on a miss. The words sit in one row just above the strip, each inside its own pad's width, so they never overlap
## one another. Pure presentation; no judgement or geometry changes. Other modes keep the plain PadView.

const BURST_S := 0.42
const MISS_S := 0.3
const INACTIVE := Color(0.075, 0.065, 0.15)  # an unlit pad when no board says otherwise
const LCD_BG := Color(0.02, 0.03, 0.07, 0.94)
const LCD_EDGE := Color(0.3, 0.85, 1.0)

var deck: StoryDeck  # for the glow sprite and the crowd energy
var energy_fn: Callable  # () -> float 0..100: the crowd energy shown on the LCD
var show_crowd_label := true  # the run turns the "CROWD" caption of the LCD off during play (RW_DEV_TEXT brings it back)
var _bursts: Dictionary = {}  # pad -> {t, color, kind}
var _glow: Dictionary = {}
var _sb := StyleBoxFlat.new()
var _skin: Dictionary = {}  # the board's colours this frame (StoryDeck.skin)
var _plate := StyleBoxFlat.new()
static var _soft_glow: Texture2D  # a radial glow for boards whose world has no "glow" sprite
static var draw_usec := 0  # CPU time spent recording the strip's draw commands, deck included (tools/art/a3_drawcost.gd reads it)


func _draw() -> void:
	var t0 := Time.get_ticks_usec()
	_skin = deck.skin(self) if deck != null else {}
	super._draw()
	draw_usec += Time.get_ticks_usec() - t0


func setup_skin(p_deck: StoryDeck) -> void:
	deck = p_deck
	_glow = deck.assets.sprite("glow") if deck != null and deck.assets != null else {}
	if _glow.is_empty() or _glow["tex"] == null:
		_glow = {"tex": soft_glow()}


## A soft round glow (white centre to transparent edge), made once.
static func soft_glow() -> Texture2D:
	if _soft_glow == null:
		var g := Gradient.new()
		g.set_color(0, Color(1, 1, 1, 1))
		g.set_color(1, Color(1, 1, 1, 0))
		g.add_point(0.45, Color(1, 1, 1, 0.45))
		var t := GradientTexture2D.new()
		t.gradient = g
		t.fill = GradientTexture2D.FILL_RADIAL
		t.fill_from = Vector2(0.5, 0.5)
		t.fill_to = Vector2(1.0, 0.5)
		t.width = 64
		t.height = 64
		_soft_glow = t
	return _soft_glow


func _sk(key: String, fallback: Color) -> Color:
	return StoryDeck.color_of(_skin, key, fallback)


func show_feedback(pad: int, text: String, color: Color, wall: float) -> void:
	super.show_feedback(pad, text, color, wall)
	var kind := "miss" if text == "MISS" else ("soft" if text in ["·", "LET GO"] else "hit")
	_bursts[pad] = {"t": wall, "color": color, "kind": kind, "perfect": text == "PERFECT" or text == "HELD"}


func _palette() -> Dictionary:
	return HC_COLOR if high_contrast else FAMILY_COLOR


func _box(r: Rect2, col: Color, radius: float, border := 0.0, border_col := Color.TRANSPARENT, fill := true) -> void:
	_sb.bg_color = col
	_sb.draw_center = fill
	_sb.border_color = border_col
	_sb.set_border_width_all(int(border))
	_sb.set_corner_radius_all(int(radius))
	_sb.anti_aliasing = true
	draw_style_box(_sb, r)


func _glow_at(c: Vector2, half: Vector2, col: Color) -> void:
	if _glow.is_empty() or _glow["tex"] == null or col.a <= 0.003:
		return
	var tex: Texture2D = _glow["tex"]
	draw_texture_rect(tex, Rect2(c - half, half * 2.0), false, col)


func _onset_pulse(pad: int, now: float) -> float:
	var list: Array = _pad_notes[pad]
	var c: int = _cursor[pad]
	while c < list.size() and float(level.notes[list[c]]["end_time" if level.notes[list[c]]["type"] == "hold" else "time"]) < now - 0.2:
		c += 1
	_cursor[pad] = c
	var pulse := 0.0
	for k in range(c, mini(c + 6, list.size())):
		var dt: float = float(level.notes[list[k]]["time"]) - now
		if dt > 0.0:
			break
		if dt > -PULSE_S * 1.6:
			pulse = maxf(pulse, 1.0 + dt / (PULSE_S * 1.6))
	return pulse


var slot_fn: Callable  # (pad, rect, now) -> {} or {mix 0..1, rect?, skip?, color?, lit?, down?, scale?, glyph?: Callable(ci, face, alpha, base, lit)}: an activity's control in the slot (RunActivityInput.slot)
var _glyph_a := 1.0  # the pad's own glyph and words are drawn at this alpha (1 - the control's mix)


func _draw_pad(pad: int, r: Rect2, now: float, tick: int, wall: float) -> void:
	var ov: Dictionary = slot_fn.call(pad, r, now) if slot_fn.is_valid() else {}  # an activity's control standing in this slot (contract 10: the frame stays, the glyph cross-fades)
	if bool(ov.get("skip", false)):
		return
	var mix := clampf(float(ov.get("mix", 0.0)), 0.0, 1.0)
	if ov.has("rect"):
		r = ov["rect"]
	var fam := _family_at(pad, tick)
	var base: Color = _palette().get(fam, Color(0.45, 0.47, 0.5))
	var active := not fam.is_empty()
	var s := minf(r.size.x, r.size.y)
	var radius := s * 0.13
	var pulse := _onset_pulse(pad, now)
	var hold := float(holding_fn.call(pad, now)) if holding_fn.is_valid() else -1.0
	var down: bool = button_down.get(pad, false)
	if mix > 0.0:  # the control's look takes over: its colour, its lit state and its press; the cues' pulse and hold fade out
		var cc: Color = ov.get("color", base)
		base = base.lerp(cc, mix) if active else cc
		if mix >= 0.5:
			active = bool(ov.get("lit", true))
			down = bool(ov.get("down", false))
			hold = -1.0
		pulse *= 1.0 - mix
		var sc := float(ov.get("scale", 1.0))
		if sc != 1.0:
			var c0 := r.get_center()
			draw_set_transform(c0 - c0 * sc, 0.0, Vector2(sc, sc))
	_glyph_a = 1.0 - mix
	var bu: Dictionary = _bursts.get(pad, {})
	var bage := wall - float(bu.get("t", -10.0))
	var miss := 0.0
	if not bu.is_empty() and bu["kind"] == "miss" and bage < MISS_S:
		miss = 1.0 - bage / MISS_S
	var shake := Vector2.ZERO
	if miss > 0.0 and not reduced_effects:
		shake.x = sin(bage * 70.0) * 3.0 * miss
	var press := (s * 0.012 if down else 0.0)
	var face := Rect2(r.position + shake + Vector2(0, press), r.size)
	var lit := 0.0  # how brightly the pad's LEDs shine 0..1
	if active:
		lit = 0.32 + 0.68 * pulse
		if down:
			lit = maxf(lit, 0.75)
		if hold >= 0.0:
			lit = maxf(lit, 0.6 + 0.3 * hold)
	if reduced_effects:
		lit = minf(lit, 0.75)
	# the well the pad sits in and the LED bleed around it
	_box(r.grow(s * 0.035), Color(0.0, 0.0, 0.03, 0.85), radius * 1.15)
	if active:
		_glow_at(r.get_center(), r.size * (0.82 + 0.1 * lit), Color(base, 0.10 + 0.32 * lit))
	# the rubber face
	var body := base.darkened(0.8) if active else _sk("pad_off", INACTIVE)
	if down:
		body = body.lightened(0.06)
	_box(face, body, radius)
	if active:  # backlight through the rubber: a soft core, brighter towards the middle
		_glow_at(face.get_center(), face.size * 0.56, Color(base.lightened(0.1), 0.18 + 0.55 * lit))
	if hold >= 0.0:  # the hold fills the pad bottom to top until its tail
		var hr := Rect2(face.position.x, face.end.y - face.size.y * hold, face.size.x, face.size.y * hold)
		_box(hr, Color(base.lightened(0.12), 0.72), radius)
		draw_line(Vector2(hr.position.x + radius * 0.6, hr.position.y), Vector2(hr.end.x - radius * 0.6, hr.position.y), Color(1, 1, 1, 0.85), 3.0)
	if miss > 0.0:
		_box(face, Color(1.0, 0.2, 0.25, 0.35 * miss), radius)
	if pulse > 0.0:
		_box(face, Color(base.lightened(0.45), (0.2 if reduced_effects else 0.45) * pulse), radius)
	var flash_at: float = _complete_flash.get(pad, -10.0)
	if wall - flash_at < 0.35:
		var a := 1.0 - (wall - flash_at) / 0.35
		_box(face.grow(s * 0.04 * (1.0 - a)), Color(base.lightened(0.5), 0.55 * a), radius)
	# a sheen along the top edge and the bevel
	_box(Rect2(face.position + Vector2(s * 0.06, s * 0.035), Vector2(face.size.x - s * 0.12, s * 0.12)), Color(1, 1, 1, 0.05 if active else 0.03), radius * 0.6)
	var rim := base.lightened(0.25 if down else 0.05) if active else _sk("pad_ring", Color(0.24, 0.2, 0.42))
	if miss > 0.0:
		rim = rim.lerp(Color(1.0, 0.35, 0.35), miss)
	_box(face, Color.TRANSPARENT, radius, (5.0 if high_contrast else 3.5) if active else 2.0, Color(rim, 1.0 if active else 0.8), false)
	_box(face.grow(-s * 0.035), Color.TRANSPARENT, radius * 0.75, 1.0, Color(1, 1, 1, 0.10 if active else 0.05), false)
	_draw_icon_skin(fam, face, base, active, lit, hold >= 0.0)
	# the burst ring of a hit
	if not bu.is_empty() and bu["kind"] == "hit" and bage < BURST_S and not reduced_effects:
		var u := bage / BURST_S
		var e := 1.0 - pow(1.0 - u, 3.0)
		var bc: Color = Color.WHITE if bu["perfect"] else base.lightened(0.3)
		_box(face.grow(s * (0.02 + 0.2 * e)), Color.TRANSPARENT, radius * (1.0 + e), maxf(1.0, 6.0 * (1.0 - u)), Color(bc, 0.85 * (1.0 - u)), false)
	_draw_texts(pad, face, base, active, tick, wall)
	_glyph_a = 1.0
	if mix > 0.0:
		var g: Callable = ov.get("glyph", Callable())
		if g.is_valid():
			g.call(self, face.grow(-s * 0.035), mix, base, active)
		draw_set_transform_matrix(Transform2D.IDENTITY)


func _draw_icon_skin(fam: String, r: Rect2, base: Color, active: bool, lit: float, holding: bool) -> void:
	if _glyph_a <= 0.0:
		return
	var c := r.get_center() + Vector2(0, r.size.y * 0.06)
	var s := minf(r.size.x, r.size.y) * 0.16
	var ga := _glyph_a
	if not active:  # an unlit pad: a dark ring and a small off LED
		var off := _sk("pad_ring", Color(0.32, 0.27, 0.55)).lightened(0.12)
		draw_arc(c, s * 0.75, 0.0, TAU, 32, Color(off, 0.55 * ga), 2.0, true)
		draw_circle(c, s * 0.16, Color(off, 0.5 * ga))
		return
	_glow_at(c, Vector2(s, s) * 2.2, Color(base, (0.25 + 0.5 * lit) * ga))
	var ic := Color.WHITE if holding else base.lightened(0.35 + 0.4 * lit)
	ic.a *= ga
	var sh := Color(0, 0, 0.05, 0.45 * ga)
	match fam:
		"kick":
			draw_circle(c + Vector2(0, 2), s, sh)
			draw_circle(c, s, ic)
			draw_circle(c, s * 0.42, Color(base.darkened(0.3), 0.55 * ga))
		"snare":
			var pts := PackedVector2Array([c + Vector2(0, -s * 1.2), c + Vector2(s * 1.2, 0), c + Vector2(0, s * 1.2), c + Vector2(-s * 1.2, 0)])
			var sp := pts.duplicate()
			for i in sp.size():
				sp[i] += Vector2(0, 2)
			draw_colored_polygon(sp, sh)
			draw_colored_polygon(pts, ic)
		"bass":
			for k in 3:
				var w := s * (2.2 - 0.5 * absf(k - 1))
				var br := Rect2(c.x - w * 0.5, c.y - s + k * s * 0.8, w, s * 0.42)
				draw_rect(Rect2(br.position + Vector2(0, 2), br.size), sh)
				draw_rect(br, ic)
		_:
			draw_arc(c, s * 0.8, 0.0, TAU, 24, Color(ic, 0.5 * ga), 2.0)


func _outlined(pos: Vector2, text: String, align: HorizontalAlignment, width: float, fs: int, col: Color, outline := 5) -> void:
	draw_string_outline(_font, pos, text, align, width, fs, outline, Color(0.02, 0.0, 0.1, col.a * 0.9))
	draw_string(_font, pos, text, align, width, fs, col)


func _draw_texts(pad: int, r: Rect2, base: Color, active: bool, tick: int, wall: float) -> void:
	if _glyph_a <= 0.0:  # (a control's pictogram has the slot: no words)
		return
	var fs := int(clampf(r.size.x * 0.1, 12.0, 21.0))
	var label := _label_at(pad, tick)
	if not label.is_empty():
		var la := (0.95 if active else 0.38) * _glyph_a
		if active and muted_fn.is_valid() and bool(muted_fn.call(_family_at(pad, tick))):
			la *= 0.5
		_outlined(Vector2(r.position.x + 4.0, r.position.y + fs + 8.0), label, HORIZONTAL_ALIGNMENT_CENTER, r.size.x - 8.0, fs,
			Color(1, 1, 1, la) if not active else Color(base.lightened(0.75), la), 4)
	if show_keys and not OS.has_feature("mobile"):
		var kc := Vector2(r.end.x - fs * 1.05, r.end.y - fs * 0.95)
		_box(Rect2(kc - Vector2(fs * 0.7, fs * 0.62), Vector2(fs * 1.4, fs * 1.24)), Color(0, 0, 0.05, 0.4 * _glyph_a), fs * 0.3)
		draw_string(_font, kc + Vector2(-fs * 0.7, fs * 0.36), key_name(pad), HORIZONTAL_ALIGNMENT_CENTER, fs * 1.4, int(fs * 0.9), Color(1, 1, 1, 0.55 * _glyph_a))


## The judgement words: one row just above the strip (over the bottom of the picture), each word inside its own pad's width on a small
## dark plate, with a short pop and fade; drawn by the note lane (a full-screen layer over everything) after the notes, so a word is never
## under a falling note. `rects` are the pads in the caller's coordinates.
func draw_feedback_layer(ci: CanvasItem, rects: Dictionary) -> void:
	var wall := float(Time.get_ticks_msec()) / 1000.0
	var strip_top := (ci.get_global_transform_with_canvas().affine_inverse() * get_global_transform_with_canvas() * Vector2.ZERO).y if ci.is_inside_tree() and is_inside_tree() else INF
	if strip_top == INF:
		for pad in rects:
			strip_top = minf(strip_top, (rects[pad] as Rect2).position.y)
	_plate.set_corner_radius_all(10)
	for pad in rects:
		var fb: Dictionary = _feedback.get(pad, {})
		if fb.is_empty() or wall >= float(fb["until"]):
			continue
		var r: Rect2 = rects[pad]
		var age := FEEDBACK_S - (float(fb["until"]) - wall)
		var a := clampf((float(fb["until"]) - wall) / (FEEDBACK_S * 0.45), 0.0, 1.0) * clampf(age / 0.05, 0.0, 1.0)
		var text := str(fb["text"])
		var fs := int(clampf(r.size.x * 0.13, 13.0, 26.0))
		var tw := _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		if tw > r.size.x - 24.0:  # a long word shrinks to its own pad's width, never into the neighbour's
			fs = maxi(10, int(fs * (r.size.x - 24.0) / tw))
			tw = _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
		var pop := 1.0 if reduced_effects else 1.0 + 0.18 * maxf(0.0, 1.0 - age / 0.08)
		var cy := strip_top - fs * 0.75 - 6.0
		ci.draw_set_transform(Vector2(r.get_center().x, cy), 0.0, Vector2(pop, pop))
		_plate.bg_color = Color(0.03, 0.02, 0.08, 0.62 * a)
		ci.draw_style_box(_plate, Rect2(-tw * 0.5 - 10.0, -fs * 0.72, tw + 20.0, fs * 1.3))
		var pos := Vector2(-r.size.x * 0.5, fs * 0.36)
		ci.draw_string_outline(_font, pos, text, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, fs, 5, Color(0.02, 0.0, 0.1, a * 0.9))
		ci.draw_string(_font, pos, text, HORIZONTAL_ALIGNMENT_CENTER, r.size.x, fs, Color(fb["color"], a))
	ci.draw_set_transform_matrix(Transform2D.IDENTITY)


## The deck's LCD between the pads: mode banner, the two-bar sequence meter and the crowd energy.
func _draw_centre(rects: Dictionary, now: float, wall: float) -> void:
	var lcd := StoryDeck.display_rect(rects, size)
	var x0 := lcd.position.x
	var w := lcd.size.x
	if w < 80.0:
		return
	var fs := int(clampf(size.y * 0.075, 12.0, 24.0))
	var edge := _sk("display_edge", LCD_EDGE)
	_box(lcd.grow(3.0), _sk("ink", Color(0.0, 0.0, 0.02)), 10.0)
	_box(lcd, Color(_sk("display_bg", LCD_BG), 0.96), 8.0, 2.0, Color(edge, 0.55))
	var scan := PackedVector2Array()  # scanlines: one call
	for k in int(lcd.size.y / 4.0):
		scan.append(Vector2(lcd.position.x + 4.0, lcd.position.y + 2.0 + k * 4.0))
		scan.append(Vector2(lcd.end.x - 4.0, lcd.position.y + 2.0 + k * 4.0))
	draw_multiline(scan, Color(_sk("display_line", Color(0.4, 0.8, 1.0)), 0.04), 1.0)
	var inner := lcd.grow(-10.0)
	if not banner_text.is_empty():
		var blink := 1.0 if reduced_effects else 0.75 + 0.25 * sin(wall * 8.0)
		_outlined(Vector2(inner.position.x, inner.position.y + fs * 1.05), banner_text, HORIZONTAL_ALIGNMENT_CENTER, inner.size.x, int(fs * 1.1), Color(1.0, 0.86, 0.45, blink), 4)
	var p: Dictionary = progress_fn.call(now) if progress_fn.is_valid() else {}
	var meter_y := inner.position.y + inner.size.y * 0.42
	var meter_h := maxf(fs * 0.62, 8.0)
	if not p.is_empty():
		var cues := maxi(int(p["cues"]), 1)
		var seg_w := minf((inner.size.x - 8.0) / float(cues), 30.0)
		var total_w := seg_w * cues
		var sx := inner.position.x + (inner.size.x - total_w) * 0.5
		var need := level.sequence_threshold * float(cues)
		var credit := float(p["credit"])
		var ok := credit >= need
		for k in cues:
			var filled := clampf(credit - float(k), 0.0, 1.0)
			var rr := Rect2(sx + k * seg_w + 2.0, meter_y, seg_w - 4.0, meter_h)
			draw_rect(rr, Color(0.12, 0.14, 0.24))
			if filled > 0.0:
				var on := Color(0.35, 1.0, 0.7) if ok else Color(0.3, 0.85, 1.0)
				draw_rect(Rect2(rr.position, Vector2(rr.size.x * filled, rr.size.y)), on)
				draw_rect(Rect2(rr.position, Vector2(rr.size.x * filled, rr.size.y * 0.3)), Color(1, 1, 1, 0.25))
		var mark := sx + need * seg_w
		draw_line(Vector2(mark, meter_y - 5.0), Vector2(mark, meter_y + meter_h + 5.0), Color(1.0, 0.85, 0.45, 0.9), 2.0)
	if energy_fn.is_valid():
		var e := clampf(float(energy_fn.call()) / 100.0, 0.0, 1.0)
		var ey := inner.end.y - meter_h * 0.8
		var bar := Rect2(inner.position.x + fs * 4.2, ey, inner.size.x - fs * 4.4, meter_h * 0.7)
		if show_crowd_label:
			draw_string(_font, Vector2(inner.position.x, ey + meter_h * 0.7), "CROWD", HORIZONTAL_ALIGNMENT_LEFT, fs * 4.0, int(fs * 0.72), Color(_sk("label", Color(0.75, 0.85, 1.0)), 0.75))
		draw_rect(bar, Color(0.12, 0.14, 0.24))
		var n := 24
		for k in n:
			var u := float(k) / float(n)
			if u >= e:
				break
			var col := Color(0.35, 0.45, 1.0).lerp(Color(1.0, 0.3, 0.8), u).lerp(Color(1.0, 0.85, 0.3), clampf((u - 0.8) / 0.2, 0.0, 1.0))
			draw_rect(Rect2(bar.position.x + bar.size.x * u + 1.0, bar.position.y, bar.size.x / float(n) - 2.0, bar.size.y), col)
	if not status_text.is_empty() and wall < status_until:
		_outlined(Vector2(x0 - 30.0, lcd.end.y + fs * 1.25), status_text, HORIZONTAL_ALIGNMENT_CENTER, w + 60.0, int(fs * 0.85), Color(status_color, clampf(status_until - wall, 0.0, 1.0)), 4)
