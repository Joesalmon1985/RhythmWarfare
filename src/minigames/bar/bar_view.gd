class_name BarView
extends Control
## The bar as a picture (bedsit brief section 6): the counter, the customer with the order as a speech bubble of ingredient pictures (only while the order is demonstrated), the glass that
## fills one layer per ingredient, the handover or the mistake, the four ingredients on the counter, the shelf of glasses that light up as drinks are served, and the payoff. There is no text:
## every cue is a shape or a colour. Driven entirely by the activity's `state()` and the song time; it keeps no game state. Ingredient pictures are BarDraw's placeholders.
##
## The host (RunMinigameHost) mounts it full-rect in the stage's low-res viewport and sets `now_fn`, `beat_s`, `reduced`, `high_contrast`, `state_fn` and `screen_size`, then calls `hit(local_pos)`
## with a tap in screen pixels: the four ingredients on the counter ("ing:<i>") and the door ("exit") answer, so touching a bottle is the same press as the control in the pad strip.
## The picture is laid out on a 640 x 190 canvas, scaled to fit and centred; the wall and floor colour fill any rest of the view.

const VW := 640.0
const VH := 190.0
const COUNTER_Y := 132.0
const CUSTOMER_X := 96.0
const HANDOVER_X := 140.0
const GLASS_X := 250.0
const GLASS_H := 44.0
const BARTENDER_X := 352.0
const SHELF_Y := 46.0
const ING_X := [446.0, 496.0, 546.0, 596.0]
const EXIT_RECT := Rect2(6, 6, 30, 38)
const BOTTLE_PX := 46.0
const PALETTES := {
	"space": {"wall": "#1a1840", "wall2": "#241f56", "counter": "#3a2f6e", "top": "#6a58b8", "dot": "#c8d8ff"},
	"magic": {"wall": "#3a1f4f", "wall2": "#4d2a66", "counter": "#6a3a8f", "top": "#a26ac8", "dot": "#ffc8f0"},
	"dinos": {"wall": "#2b3a1f", "wall2": "#38492a", "counter": "#5a4a2a", "top": "#8f7a44", "dot": "#9fd86a"},
	"transport": {"wall": "#26303a", "wall2": "#313d49", "counter": "#4a4a52", "top": "#80808c", "dot": "#ffd84a"},
}
const SKIN := Color("e8b98a")
const OUTLINE := Color(0.05, 0.04, 0.08, 1.0)

var now_fn: Callable = Callable()
var state_fn: Callable = Callable()
var beat_s := 60.0 / 174.0
var reduced := false
var high_contrast := false
var screen_size := Vector2(844, 250)

var _snap: Dictionary = {}
var _now := 0.0


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	set_process(true)


func _process(_delta: float) -> void:
	queue_redraw()


# --- layout and touch ----------------------------------------------------------------------------------------------------------

## {scale, offset}: the 640 x 190 canvas inside this control.
func layout() -> Dictionary:
	var sz := size if size.x > 0.0 and size.y > 0.0 else Vector2(VW, VH)
	var s := minf(sz.x / VW, sz.y / VH)
	return {"scale": s, "offset": (sz - Vector2(VW, VH) * s) * 0.5}


## The touch rectangles live now, id to Rect2 in canvas coordinates (640 x 190): the ingredients on the counter while the activity takes ingredients, the door whenever it may be left.
func target_rects() -> Dictionary:
	var snap := _fetch()
	var out := {}
	if snap.is_empty() or bool(snap.get("done", false)):
		return out
	var targets: Array = snap.get("targets", [])
	for i in 4:
		if (BarActivity.ING_PREFIX + str(i)) in targets:
			out[BarActivity.ING_PREFIX + str(i)] = Rect2(float(ING_X[i]) - 25.0, COUNTER_Y - 56.0, 50.0, 62.0)
	for tg: Variant in targets:
		if BarActivity.is_exit_target(str(tg)):
			out[str(tg)] = EXIT_RECT
			break
	return out


## The target under a tap (`local_pos` in screen pixels from the stage area's top-left), "" for nothing.
func hit(local_pos: Vector2) -> String:
	if screen_size.x <= 0.0 or screen_size.y <= 0.0:
		return ""
	var lay := layout()
	var p := Vector2(local_pos.x * size.x / screen_size.x, local_pos.y * size.y / screen_size.y)
	p = (p - (lay["offset"] as Vector2)) / float(lay["scale"])
	var rects := target_rects()
	var best := ""
	var best_d := INF
	for id: String in rects:
		var r: Rect2 = rects[id]
		if r.grow(4.0).has_point(p):
			var d := (p - r.get_center()).length_squared()
			if d < best_d:
				best_d = d
				best = id
	return best


func _fetch() -> Dictionary:
	_snap = state_fn.call() if state_fn.is_valid() else {}
	_now = float(now_fn.call()) if now_fn.is_valid() else float(_snap.get("t", 0.0))
	return _snap


# --- drawing -------------------------------------------------------------------------------------------------------------------

func _draw() -> void:
	var snap := _fetch()
	if snap.is_empty():
		return
	var pal: Dictionary = PALETTES.get(str(snap.get("theme", "")), PALETTES["space"])
	var lay := layout()
	var s: float = lay["scale"]
	var off: Vector2 = lay["offset"]
	var full := Rect2(Vector2.ZERO, size)
	draw_rect(full, Color(pal["wall"]), true)
	draw_set_transform(off, 0.0, Vector2(s, s))
	_draw_room(pal, snap)
	var ph := str(snap.get("phase", ""))
	var p := _now - float(snap.get("phase_t0", 0.0))
	var dur := float(snap.get("phase_dur", -1.0))
	var u := clampf(p / dur, 0.0, 1.0) if dur > 0.0 else 0.0
	var outcome := str(snap.get("outcome", ""))
	var ings: Array = snap.get("ingredients", [])
	_draw_shelf(snap, ph, p, ings)
	_draw_exit(snap)
	# the customer
	var cx := CUSTOMER_X
	var mood := "neutral"
	var bounce := 0.0
	match ph:
		"arrive":
			cx = lerpf(-40.0, CUSTOMER_X, _ease_out(clampf(p / maxf(dur, 0.001), 0.0, 1.0)))
		"demo":
			mood = "talk"
		"serve":
			if outcome == "happy":
				mood = "happy"
				bounce = absf(sin(p * 9.0)) * 4.0 if u > 0.45 and not reduced else 0.0
				if u > 0.8:
					cx = lerpf(CUSTOMER_X, -50.0, _ease_in(clampf((u - 0.8) / 0.2, 0.0, 1.0)))
			else:
				mood = "frown" if u < 0.8 else "neutral"
		"payoff":
			mood = "happy"
			bounce = absf(sin(p * 7.0)) * 5.0 if not reduced else 0.0
	_draw_customer(snap, cx, bounce, mood, p)
	_draw_bartender(snap, ph, p, u, outcome)
	# the order bubble: only while it is demonstrated
	if bool(snap.get("bubble", false)):
		_draw_bubble(snap, p, ings)
	_draw_counter(pal)
	_draw_glass_station(snap, ph, p, u, outcome, ings)
	_draw_ingredients(snap, ph, p, ings)
	if ph == "input":
		_draw_pips(snap, ings)
	if ph == "payoff" and not reduced:
		_draw_confetti(p, ings)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


func _draw_room(pal: Dictionary, snap: Dictionary) -> void:
	var theme := str(snap.get("theme", ""))
	draw_rect(Rect2(-VW, 0, VW * 3.0, COUNTER_Y), Color(pal["wall"]), true)
	draw_rect(Rect2(-VW, 70, VW * 3.0, 62), Color(pal["wall2"]), true)
	var dot: Color = Color(pal["dot"])
	for i in 26:
		var x := float((i * 97) % 640)
		var y := 6.0 + float((i * 53) % 110)
		match theme:
			"dinos":
				draw_colored_polygon(PackedVector2Array([Vector2(x, 0), Vector2(x + 6, 0), Vector2(x + 3, 12 + float(i % 4) * 6)]), Color(dot, 0.25))
			"transport":
				if i % 2 == 0:
					draw_rect(Rect2(x, 118, 14, 3), Color(dot, 0.3), true)
			_:
				draw_circle(Vector2(x, y), 1.0 + float(i % 3) * 0.6, Color(dot, 0.35))
	draw_rect(Rect2(-VW, COUNTER_Y, VW * 3.0, VH - COUNTER_Y + 80.0), Color(pal["counter"]).darkened(0.35), true)


func _draw_counter(pal: Dictionary) -> void:
	draw_rect(Rect2(-VW, COUNTER_Y, VW * 3.0, 9), Color(pal["top"]), true)
	draw_rect(Rect2(-VW, COUNTER_Y + 9, VW * 3.0, VH - COUNTER_Y), Color(pal["counter"]), true)
	draw_rect(Rect2(-VW, COUNTER_Y + 9, VW * 3.0, 3), Color(0, 0, 0, 0.25), true)
	for i in 8:
		draw_rect(Rect2(20.0 + float(i) * 86.0, COUNTER_Y + 22.0, 3, 40), Color(0, 0, 0, 0.18), true)


func _draw_exit(snap: Dictionary) -> void:
	var targets: Array = snap.get("targets", [])
	var can := false
	for tg: Variant in targets:
		if BarActivity.is_exit_target(str(tg)):
			can = true
	if not can:
		return
	var r := EXIT_RECT
	draw_rect(r, Color(0.08, 0.07, 0.1, 0.8), true)
	draw_rect(r, Color(0.85, 0.85, 0.95, 0.85), false, 2.0)
	draw_rect(Rect2(r.position + Vector2(5, 5), Vector2(11, 28)), Color(0.55, 0.38, 0.2), true)  # the door
	draw_circle(r.position + Vector2(13, 20), 1.4, Color(1, 0.9, 0.5))
	draw_colored_polygon(PackedVector2Array([r.position + Vector2(18, 13), r.position + Vector2(26, 19), r.position + Vector2(18, 25)]), Color(0.9, 0.95, 1.0))  # the way out


func _draw_shelf(snap: Dictionary, ph: String, p: float, ings: Array) -> void:
	var drinks := int(snap.get("drinks", 4))
	var served := int(snap.get("served", 0))
	draw_rect(Rect2(404, SHELF_Y, 224, 5), Color(0.35, 0.24, 0.14), true)
	var step := 214.0 / float(maxi(drinks, 1))
	for i in drinks:
		var gx := 418.0 + step * float(i) + step * 0.12
		var lit := i < served
		var col := Color(ings[i % 4]["color"]) if not ings.is_empty() else Color(1, 0.9, 0.4)
		var pulse := 1.0
		if ph == "payoff":
			pulse = 0.75 + 0.25 * sin(p * 8.0 + float(i)) if not reduced else 1.0
		var pos := Vector2(gx, SHELF_Y)
		if lit:
			draw_circle(pos + Vector2(0, -14), 17.0 * pulse, Color(col, 0.22))
		_draw_small_glass(pos, 0.5, col if lit else Color(0.5, 0.55, 0.65), 1.0 if lit else 0.0)


## A small glass standing at `pos` (bottom centre), filled to `fill` of its height with `col`.
func _draw_small_glass(pos: Vector2, k: float, col: Color, fill: float) -> void:
	var h := GLASS_H * k
	var tw := 15.0 * k
	var bw := 12.0 * k
	var body := PackedVector2Array([pos + Vector2(-tw, -h), pos + Vector2(tw, -h), pos + Vector2(bw, 0), pos + Vector2(-bw, 0)])
	draw_colored_polygon(body, Color(0.8, 0.9, 1.0, 0.25))
	if fill > 0.0:
		var fh := h * 0.8 * fill
		draw_colored_polygon(PackedVector2Array([pos + Vector2(-lerpf(bw, tw, fh / h) + 1.0, -fh), pos + Vector2(lerpf(bw, tw, fh / h) - 1.0, -fh), pos + Vector2(bw - 1.0, -1), pos + Vector2(-bw + 1.0, -1)]), col)
	draw_polyline(PackedVector2Array([body[0], body[3], body[2], body[1]]), Color(0.9, 0.95, 1.0, 0.9), 2.0 if high_contrast else 1.5)


func _draw_customer(snap: Dictionary, cx: float, bounce: float, mood: String, p: float) -> void:
	var look: Dictionary = snap.get("customer", {})
	var body: Color = look.get("body", Color("6fcf7f"))
	var kind := str(look.get("kind", "antenna"))
	var hy := 70.0 - bounce
	var ow := 3.0 if high_contrast else 2.0
	draw_rect(Rect2(cx - 27, hy + 20, 54, 70), OUTLINE, true)
	draw_rect(Rect2(cx - 25, hy + 22, 50, 70), body.darkened(0.2), true)
	draw_circle(Vector2(cx, hy), 24.0 + ow * 0.5, OUTLINE)
	draw_circle(Vector2(cx, hy), 22.0, body)
	match kind:
		"antenna":
			draw_line(Vector2(cx, hy - 22), Vector2(cx + 7, hy - 36), OUTLINE, 2.0)
			draw_circle(Vector2(cx + 7, hy - 37), 4.0, Color(1.0, 0.9, 0.4))
		"hat":
			draw_colored_polygon(PackedVector2Array([Vector2(cx - 20, hy - 14), Vector2(cx + 20, hy - 14), Vector2(cx + 4, hy - 48)]), Color(0.3, 0.2, 0.6))
			draw_rect(Rect2(cx - 24, hy - 16, 48, 4), Color(0.25, 0.16, 0.5), true)
			draw_circle(Vector2(cx + 2, hy - 28), 2.5, Color(1.0, 0.9, 0.4))
		"crest":
			for k in 3:
				var x := cx - 12.0 + float(k) * 12.0
				draw_colored_polygon(PackedVector2Array([Vector2(x - 5, hy - 18), Vector2(x + 5, hy - 18), Vector2(x, hy - 36)]), body.lightened(0.25))
		"cap":
			draw_colored_polygon(_half_disc(Vector2(cx, hy - 10), 22.0), Color(0.85, 0.2, 0.2))
			draw_rect(Rect2(cx - 2, hy - 14, 28, 5), Color(0.65, 0.12, 0.12), true)
	var blink := (not reduced) and fmod(p, 3.1) > 3.0
	for sx in [-8.0, 8.0]:
		draw_circle(Vector2(cx + sx, hy - 3), 5.5, Color(0.97, 0.97, 1.0))
		if not blink:
			draw_circle(Vector2(cx + sx + 1.0, hy - 2), 2.6, OUTLINE)
	match mood:
		"happy":
			draw_arc(Vector2(cx, hy + 6), 9.0, 0.15 * PI, 0.85 * PI, 10, OUTLINE, 2.5)
			draw_circle(Vector2(cx - 15, hy + 5), 3.0, Color(1.0, 0.5, 0.55, 0.7))
			draw_circle(Vector2(cx + 15, hy + 5), 3.0, Color(1.0, 0.5, 0.55, 0.7))
		"frown":
			draw_arc(Vector2(cx, hy + 17), 9.0, 1.15 * PI, 1.85 * PI, 10, OUTLINE, 2.5)
			draw_line(Vector2(cx - 13, hy - 14), Vector2(cx - 4, hy - 10), OUTLINE, 2.5)
			draw_line(Vector2(cx + 13, hy - 14), Vector2(cx + 4, hy - 10), OUTLINE, 2.5)
		"talk":
			var open := 2.0 + (absf(sin(p * 8.0)) * 3.0 if not reduced else 2.0)
			draw_rect(Rect2(cx - 5, hy + 8, 10, open), OUTLINE, true)
		_:
			draw_line(Vector2(cx - 6, hy + 10), Vector2(cx + 6, hy + 10), OUTLINE, 2.5)


func _half_disc(c: Vector2, r: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in 13:
		var a := PI + PI * float(i) / 12.0
		out.append(c + Vector2(cos(a) * r, sin(a) * r))
	return out


func _draw_bartender(snap: Dictionary, ph: String, p: float, u: float, outcome: String) -> void:
	var cx := BARTENDER_X
	var hy := 74.0
	draw_rect(Rect2(cx - 23, hy + 16, 46, 60), OUTLINE, true)
	draw_rect(Rect2(cx - 21, hy + 18, 42, 60), Color(0.93, 0.93, 0.97), true)  # shirt
	draw_rect(Rect2(cx - 21, hy + 30, 42, 50), Color(0.2, 0.2, 0.3), true)  # waistcoat
	draw_line(Vector2(cx, hy + 18), Vector2(cx, hy + 40), Color(0.93, 0.93, 0.97), 2.0)
	draw_circle(Vector2(cx, hy), 17.0, OUTLINE)
	draw_circle(Vector2(cx, hy), 15.5, SKIN)
	draw_rect(Rect2(cx - 16, hy - 17, 32, 9), Color(0.2, 0.15, 0.15), true)  # hair
	draw_circle(Vector2(cx - 5, hy - 1), 2.0, OUTLINE)
	draw_circle(Vector2(cx + 5, hy - 1), 2.0, OUTLINE)
	var shoulder := Vector2(cx - 18, hy + 26)
	var hand := Vector2(cx - 24, hy + 52)
	var raised := ph == "payoff"
	var mistake := ph == "serve" and outcome == "mistake"
	var happy := ph == "serve" and outcome == "happy"
	if raised:
		hand = Vector2(cx + 22, hy - 30 + (sin(p * 6.0) * 2.0 if not reduced else 0.0))
		shoulder = Vector2(cx + 16, hy + 26)
	elif happy and u < 0.5:
		hand = Vector2(GLASS_X + 20.0 + 70.0 * _ease_out(clampf(u / 0.5, 0.0, 1.0)), COUNTER_Y - 10.0)
		hand.x = minf(hand.x, cx - 14.0)
		shoulder = Vector2(cx - 18, hy + 26)
	elif mistake and u > 0.4 and u < 0.7:
		hand = Vector2(cx - 40, hy + 38)  # the shrug
	draw_line(shoulder, hand, OUTLINE, 7.0)
	draw_line(shoulder, hand, Color(0.93, 0.93, 0.97), 4.5)
	draw_circle(hand, 4.0, SKIN)
	if raised:
		_draw_small_glass(hand + Vector2(0, 6), 0.7, Color(1.0, 0.85, 0.3), 1.0)
		if not reduced:
			var a := fmod(p * 4.0, 1.0)
			draw_circle(hand + Vector2(-9, -20 - a * 10.0), 1.8, Color(1, 1, 0.8, 1.0 - a))


func _draw_bubble(snap: Dictionary, p: float, ings: Array) -> void:
	var recipe: Array = snap.get("recipe", [])
	var n := recipe.size()
	var shown := int(snap.get("shown", -1))
	var pop := clampf(p / 0.15, 0.0, 1.0)
	var c := Vector2(232.0, 46.0)
	var half := Vector2(100.0, 40.0) * (0.6 + 0.4 * pop)
	var r := Rect2(c - half, half * 2.0)
	draw_colored_polygon(PackedVector2Array([Vector2(122, 70), Vector2(150, 60), Vector2(150, 78)]), OUTLINE)
	draw_rect(r.grow(2.5), OUTLINE, true)
	draw_rect(r, Color(0.98, 0.97, 0.92), true)
	draw_colored_polygon(PackedVector2Array([Vector2(126, 70), Vector2(152, 62), Vector2(152, 76)]), Color(0.98, 0.97, 0.92))
	if pop < 1.0:
		return
	var show_s := float(snap.get("show_s", 0.8))
	for i in n:
		var cx := c.x + (float(i) - float(n - 1) * 0.5) * 62.0
		var sc := Vector2(cx, c.y)
		if i > shown:
			draw_arc(sc, 22.0, 0.0, TAU, 20, Color(0.55, 0.55, 0.6), 2.0)
			draw_circle(sc, 3.0, Color(0.6, 0.6, 0.65))
			continue
		var e: Dictionary = ings[int(recipe[i])]
		var since := p - float(i) * show_s
		var k := 1.0 + (0.25 * sin(clampf(since / 0.3, 0.0, 1.0) * PI) if not reduced else 0.0)
		var size_px := 44.0 * k
		var tex := BarDraw.texture(str(e["shape"]), e["color"])
		draw_texture_rect(tex, Rect2(sc - Vector2(size_px, size_px) * 0.5, Vector2(size_px, size_px)), false)
		if i == shown:
			draw_arc(sc, 26.0, 0.0, TAU, 24, Color(1.0, 0.8, 0.2), 3.0)


func _glass_pos(snap: Dictionary, ph: String, p: float, u: float, outcome: String) -> Dictionary:
	var pos := Vector2(GLASS_X, COUNTER_Y)
	var rot := 0.0
	var k := 1.0
	var alpha := 1.0
	var shake := 0.0
	if ph == "arrive":
		k = _ease_out(clampf(p / 0.4, 0.0, 1.0))
	elif ph == "serve" and outcome == "happy":
		var slide := clampf((u - 0.15) / 0.45, 0.0, 1.0)
		pos.x = lerpf(GLASS_X, HANDOVER_X, _ease_in_out(slide))
		pos.y -= sin(slide * PI) * 8.0
		if u > 0.8:
			pos.x = lerpf(HANDOVER_X, -50.0, _ease_in(clampf((u - 0.8) / 0.2, 0.0, 1.0)))
	elif ph == "serve" and outcome == "mistake":
		if u < 0.4:
			shake = (sin(p * 40.0) * 2.5 if not reduced else 0.0)
		elif u < 0.65:
			var f := _ease_in_out((u - 0.4) / 0.25)
			rot = f * 1.75
			pos += Vector2(70.0, 14.0) * f
			alpha = 1.0 - f
		elif u < 0.8:
			alpha = 0.0
		else:
			k = _ease_out((u - 0.8) / 0.2)
	elif ph == "payoff":
		pos.x = HANDOVER_X
	pos.x += shake
	return {"pos": pos, "rot": rot, "k": k, "alpha": alpha}


func _draw_glass_station(snap: Dictionary, ph: String, p: float, u: float, outcome: String, ings: Array) -> void:
	var g := _glass_pos(snap, ph, p, u, outcome)
	var recipe: Array = snap.get("recipe", [])
	var n := maxi(recipe.size(), 1)
	var entries: Array = snap.get("glass", [])
	var fresh := ph == "serve" and outcome == "mistake" and u >= 0.8
	var layers: Array = []
	if not fresh and ph in ["input", "serve", "payoff"]:
		for i in entries.size():
			var e: Dictionary = entries[i]
			var col: Color = ings[int(e["ing"])]["color"]
			layers.append({"color": col, "frac": clampf((_now - float(e["t"])) / 0.18, 0.0, 1.0), "wrong": bool(e["wrong"])})
	if ph == "payoff" or (ph == "serve" and outcome == "happy"):
		pass
	var pos: Vector2 = g["pos"]
	# a puddle where a drink overflowed
	if ph == "serve" and outcome == "mistake" and u > 0.15 and u < 0.95 and not entries.is_empty() and bool(entries[-1]["wrong"]):
		var pc: Color = ings[int(entries[-1]["ing"])]["color"]
		var pw := 22.0 * _ease_out(clampf((u - 0.15) / 0.2, 0.0, 1.0)) * (1.0 - 0.5 * clampf((u - 0.8) / 0.2, 0.0, 1.0))
		draw_colored_polygon(_e_poly(Vector2(GLASS_X + 4.0, COUNTER_Y + 4.0), pw, 3.5), Color(pc, 0.85))
	var kk: float = g["k"]
	if kk <= 0.01 or float(g["alpha"]) <= 0.01:
		return
	var s: float = layout()["scale"]
	var off: Vector2 = layout()["offset"]
	var m := Transform2D(0.0, Vector2(s, s), 0.0, off) * Transform2D(float(g["rot"]), Vector2(kk, kk), 0.0, pos)
	draw_set_transform_matrix(m)
	var a: float = g["alpha"]
	var body := PackedVector2Array([Vector2(-15, -GLASS_H), Vector2(15, -GLASS_H), Vector2(12, 0), Vector2(-12, 0)])
	draw_colored_polygon(body, Color(0.8, 0.9, 1.0, 0.22 * a))
	var layer_h := (GLASS_H - 6.0) / float(n)
	for i in layers.size():
		var L: Dictionary = layers[i]
		var y0 := -3.0 - layer_h * float(i)
		var y1 := y0 - layer_h * float(L["frac"])
		var col: Color = L["color"]
		col.a = a
		draw_colored_polygon(PackedVector2Array([Vector2(-_hw(y1) + 1.5, y1), Vector2(_hw(y1) - 1.5, y1), Vector2(_hw(y0) - 1.5, y0), Vector2(-_hw(y0) + 1.5, y0)]), col)
		if bool(L["wrong"]) and float(L["frac"]) >= 1.0:  # the mistake overflows: a stream down the side
			var drip := clampf((_now - float(entries[i]["t"]) - 0.18) / 0.3, 0.0, 1.0)
			draw_colored_polygon(PackedVector2Array([Vector2(13, -GLASS_H + 2), Vector2(18, -GLASS_H + 2), Vector2(17, -GLASS_H + 2 + (GLASS_H - 2) * drip), Vector2(14, -GLASS_H + 2 + (GLASS_H - 2) * drip)]), col)
			draw_circle(Vector2(0, -GLASS_H), 12.0, Color(col, 0.9 * a))
	draw_polyline(PackedVector2Array([body[0], body[3], body[2], body[1]]), Color(0.92, 0.97, 1.0, a), 2.5 if high_contrast else 2.0)
	draw_line(Vector2(-10, -GLASS_H + 6), Vector2(-9, -GLASS_H * 0.4), Color(1, 1, 1, 0.45 * a), 1.5)
	if ph == "serve" and outcome == "happy" and u > 0.5 and not reduced:  # a sparkle on the full drink
		var sp := fmod(p * 3.0, 1.0)
		draw_circle(Vector2(10, -GLASS_H - 6.0 - sp * 6.0), 1.8, Color(1, 1, 0.8, 1.0 - sp))
	draw_set_transform(off, 0.0, Vector2(s, s))


func _hw(y: float) -> float:
	return lerpf(12.0, 15.0, clampf(-y / GLASS_H, 0.0, 1.0))


func _e_poly(c: Vector2, rx: float, ry: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	for i in 16:
		var a := TAU * float(i) / 16.0
		out.append(c + Vector2(cos(a) * rx, sin(a) * ry))
	return out


func _draw_ingredients(snap: Dictionary, ph: String, p: float, ings: Array) -> void:
	var last: Dictionary = snap.get("last_press", {})
	var targets: Array = snap.get("targets", [])
	var recipe: Array = snap.get("recipe", [])
	var shown := int(snap.get("shown", -1))
	for i in 4:
		var e: Dictionary = ings[i]
		var cx: float = ING_X[i]
		var hop := 0.0
		var wrong_flash := false
		if str(last.get("id", "")) == BarActivity.ING_PREFIX + str(i):
			var since := _now - float(last.get("t", -100.0))
			if since >= 0.0 and since < 0.25:
				hop = sin(since / 0.25 * PI) * 9.0
				wrong_flash = i == int(snap.get("wrong", -1)) and ph == "serve"
		var live := (BarActivity.ING_PREFIX + str(i)) in targets
		var base := Vector2(cx, COUNTER_Y - BOTTLE_PX * 0.5 - 1.0 - hop)
		draw_circle(Vector2(cx, COUNTER_Y - 1.0), 18.0, Color(0, 0, 0, 0.2))
		if ph == "demo" and shown >= 0 and shown < recipe.size() and int(recipe[shown]) == i:
			draw_arc(base, 28.0, 0.0, TAU, 24, Color(1.0, 0.8, 0.2), 3.0)
		draw_texture_rect(BarDraw.texture(str(e["shape"]), e["color"]), Rect2(base - Vector2(BOTTLE_PX, BOTTLE_PX) * 0.5, Vector2(BOTTLE_PX, BOTTLE_PX)), false, Color(1, 1, 1, 1.0 if live or ph == "demo" else 0.75))
		if wrong_flash:
			draw_arc(base, 28.0, 0.0, TAU, 24, Color(1.0, 0.2, 0.2), 3.5)
			draw_line(base + Vector2(-14, -14), base + Vector2(14, 14), Color(1.0, 0.2, 0.2), 4.0)
			draw_line(base + Vector2(14, -14), base + Vector2(-14, 14), Color(1.0, 0.2, 0.2), 4.0)


## The steps right so far, over the glass: one pip per ingredient of the order, filled with the picture pressed.
func _draw_pips(snap: Dictionary, ings: Array) -> void:
	var n := int(snap.get("len", 2))
	var pos := int(snap.get("pos", 0))
	var recipe: Array = snap.get("recipe", [])
	for i in n:
		var c := Vector2(GLASS_X + (float(i) - float(n - 1) * 0.5) * 18.0, COUNTER_Y - GLASS_H - 14.0)
		draw_circle(c, 7.0, OUTLINE)
		if i < pos:
			var e: Dictionary = ings[int(recipe[i])]
			draw_circle(c, 5.5, e["color"])
		else:
			draw_circle(c, 5.5, Color(0.25, 0.25, 0.3))


func _draw_confetti(p: float, ings: Array) -> void:
	for i in 24:
		var x := float((i * 71) % 600) + 20.0
		var y := fmod(float((i * 37) % 120) + p * (30.0 + float(i % 5) * 8.0), 130.0)
		var col: Color = ings[i % 4]["color"] if not ings.is_empty() else Color.WHITE
		draw_rect(Rect2(x, y, 3, 3), Color(col, 0.9), true)


# --- easing --------------------------------------------------------------------------------------------------------------------

static func _ease_out(x: float) -> float:
	return 1.0 - (1.0 - x) * (1.0 - x)


static func _ease_in(x: float) -> float:
	return x * x


static func _ease_in_out(x: float) -> float:
	return x * x * (3.0 - 2.0 * x)
