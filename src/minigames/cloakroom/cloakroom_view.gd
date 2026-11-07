class_name CloakroomView
extends Control
## The cloakroom as a picture (docs/briefs/BEDSIT_RAVES_BRIEF.md section 5): the counter with the symbol tag, the coat rail (one coat per coat still to come), the customers in
## their queue, the attendant, and the counter lamp. Driven entirely by CloakroomActivity.state() and the song time; it owns no game state. NO WORDS anywhere: every cue is a
## shape, a colour or a movement. PLACEHOLDER art (CloakroomArt): shapes, not the art standard.
##
## The host (RunMinigameHost) mounts it full-rect in the stage's low-res viewport and sets now_fn, beat_s, reduced, high_contrast, state_fn, screen_size and calls hit().
## It draws in a 640 x 230 design space, uniformly scaled and centred; `hit` only ever answers "exit" (the door sign in the top-left corner): the two answer controls are
## the host's controls layer in the pad strip. The first three trials show the previous symbol fading beside the current one; the demonstration shows the answer.

const W := 640.0
const H := 230.0
const FEEDBACK_S := 1.0
const WALK_IN_S := 0.35
const TAG := Rect2(300, 56, 98, 98)
const COUNTER_Y := 156.0
const DOOR := Rect2(8, 8, 26, 34)

var now_fn: Callable = Callable()
var state_fn: Callable = Callable()
var beat_s := 60.0 / 174.0
var reduced := false
var high_contrast := false
var screen_size := Vector2(844, 250)

var _s := 1.0
var _off := Vector2.ZERO
var _look_theme := "?none"
var _look: Dictionary = {}
var _snap: Dictionary = {}
var _now := 0.0


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	clip_contents = true


func _process(_delta: float) -> void:
	queue_redraw()


## The target under a tap (`local` in screen pixels, relative to the stage area's top-left): "exit" on the door sign, else "".
func hit(local: Vector2) -> String:
	var area := screen_size if screen_size.x > 0.0 and screen_size.y > 0.0 else size
	var v := Vector2(local.x / area.x * size.x, local.y / area.y * size.y)
	_fit()
	var d := (v - _off) / _s
	return "exit" if DOOR.grow(6.0).has_point(d) else ""


func _fit() -> void:
	_s = maxf(minf(size.x / W, size.y / H), 0.05)
	_off = ((size - Vector2(W, H) * _s) * 0.5).floor()


func _draw() -> void:
	_fit()
	_snap = state_fn.call() if state_fn.is_valid() else {}
	_now = float(now_fn.call()) if now_fn.is_valid() else float(_snap.get("t", 0.0))
	var th := str(_snap.get("theme", ""))
	if th != _look_theme:
		_look_theme = th
		_look = CloakroomArt.look(th)
	draw_set_transform(_off, 0.0, Vector2(_s, _s))
	_room()
	if _snap.is_empty():
		return
	var phase := str(_snap.get("phase", "demo"))
	var done := phase in ["payoff", "done"]
	_rail(done)
	_queue(done)
	_attendant(phase)
	_counter()
	_tag(phase)
	_lamp(phase)
	_customer(phase)
	_door()
	_hints(phase)
	if phase == "payoff" and not reduced:
		_sparkles()
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)


# --- the room ---------------------------------------------------------------------------------------------------------------------

func _room() -> void:
	var wall: Color = _look.get("wall", Color("1a1f3d"))
	var floor_c: Color = _look.get("floor", Color("272a4a"))
	draw_rect(Rect2(-W, -H, W * 3.0, H * 3.0), wall.darkened(0.35))
	draw_rect(Rect2(0, 0, W, 170), wall)
	for i in 8:  # (wall panel seams)
		draw_rect(Rect2(float(i) * 84.0 + 20.0, 0, 2, 170), wall.darkened(0.2))
	draw_rect(Rect2(0, 170, W, H - 170), floor_c)
	draw_rect(Rect2(0, 168, W, 3), floor_c.lightened(0.25))


func _rail(done: bool) -> void:
	var n := int(_snap.get("remaining", 0))
	var hung := 0 if done else maxi(n - 1, 0)  # (the customer at the counter holds the coat being dealt with)
	var coats := int(_snap.get("coats", 8))
	draw_rect(Rect2(14, 50, 212, 3), Color("c0c0c8"))
	draw_rect(Rect2(12, 50, 4, 66), Color("8a8a96"))
	draw_rect(Rect2(224, 50, 4, 66), Color("8a8a96"))
	var step := minf(24.0, 196.0 / float(maxi(coats, 1)))
	var palette := [Color("e8503a"), Color("3fa0ff"), Color("ffd93d"), Color("3fe89a"), Color("e45bd4"), Color("ff9f40"), Color("a77fe8"), Color("5ec8f2")]
	for k in hung:
		var x := 26.0 + step * float(k)
		var sway := 0.0 if reduced else sin(_now * 1.6 + float(k)) * 1.2
		_coat(Vector2(x + sway, 54), palette[k % palette.size()], 1.0)


## A coat on a hanger hanging from `top` (the hook point).
func _coat(top: Vector2, col: Color, k: float) -> void:
	var ink := Color("1a1626")
	draw_line(top, top + Vector2(0, 5) * k, ink, 2.0)
	draw_colored_polygon(PackedVector2Array([top + Vector2(-9, 8) * k, top + Vector2(9, 8) * k, top + Vector2(0, 5) * k]), ink)
	draw_colored_polygon(PackedVector2Array([top + Vector2(-8, 9) * k, top + Vector2(8, 9) * k, top + Vector2(11, 38) * k, top + Vector2(-11, 38) * k]), ink)
	draw_colored_polygon(PackedVector2Array([top + Vector2(-7, 9) * k, top + Vector2(7, 9) * k, top + Vector2(10, 37) * k, top + Vector2(-10, 37) * k]), col)
	draw_rect(Rect2(top + Vector2(-1, 11) * k, Vector2(2, 24) * k), col.darkened(0.3))


func _queue(done: bool) -> void:
	var n := mini(maxi(int(_snap.get("remaining", 0)) - 1, 0), 3)
	if done:
		return
	var custs: Array = _look.get("customers", [])
	if custs.is_empty():
		return
	var base := int(_snap.get("customer", 0))
	for k in n:
		var who: Dictionary = custs[(base + 1 + k) % custs.size()]
		_person(Vector2(566.0 + float(k) * 34.0, 198.0 - float(k) * 3.0), 0.62 - float(k) * 0.04, who, "waiting", false, 0.0, true)


func _attendant(phase: String) -> void:
	var who: Dictionary = _look.get("attendant", {"kind": "alien", "body": Color("5ec8f2"), "skin": Color("a8e6ff"), "extra": Color("e8503a")})
	var wave := phase in ["payoff", "done"]
	var mood := "happy" if wave or (phase == "process" and bool((_snap.get("last", {}) as Dictionary).get("correct", true))) else "waiting"
	if phase == "process" and not bool((_snap.get("last", {}) as Dictionary).get("correct", true)):
		mood = "waiting"
	_person(Vector2(262, 176), 0.9, who, mood, false, 0.0, false, wave)


func _counter() -> void:
	var c: Color = _look.get("counter", Color("5a5f8a"))
	draw_rect(Rect2(150, COUNTER_Y, 400, 74), Color("1a1626"))
	draw_rect(Rect2(152, COUNTER_Y + 2, 396, 70), c.darkened(0.25))
	draw_rect(Rect2(144, COUNTER_Y - 6, 412, 12), Color("1a1626"))
	draw_rect(Rect2(146, COUNTER_Y - 4, 408, 8), c.lightened(0.15))
	for i in 5:
		draw_rect(Rect2(164.0 + float(i) * 78.0, COUNTER_Y + 14, 62, 44), c.darkened(0.4))


# --- the tag: the current symbol, the previous one fading beside it, the feedback ---------------------------------------------------

func _tag(phase: String) -> void:
	var cur := str(_snap.get("current", ""))
	var board := Color("f6f1e4") if not high_contrast else Color.WHITE
	var ink := Color("1a1626")
	var shake := Vector2.ZERO
	var fb := _feedback_age()
	var last: Dictionary = _snap.get("last", {})
	if fb >= 0.0 and fb < 0.45 and not bool(last.get("correct", true)) and not reduced:
		shake = Vector2(sin(fb * 60.0) * 4.0 * (1.0 - fb / 0.45), 0)
	var r := Rect2(TAG.position + shake, TAG.size)
	draw_rect(r.grow(4.0), ink)
	draw_rect(r, board)
	draw_rect(r.grow(-5.0), board.darkened(0.06))
	draw_line(Vector2(r.get_center().x, r.position.y - 4), Vector2(r.get_center().x, 40), Color("c0c0c8"), 2.0)  # (the cord it hangs by)
	if cur != "":
		var k := 1.0
		if not reduced and phase == "await":
			var age := _now - float(_snap.get("phase_t0", 0.0))
			k = 1.0 + clampf(1.0 - age / 0.25, 0.0, 1.0) * 0.18
		var side := 64.0 * 1.05 * k
		draw_texture_rect(CloakroomArt.symbol_texture(cur), Rect2(r.get_center() - Vector2(side, side) * 0.5, Vector2(side, side)), false)
	var prev := str(_snap.get("previous", ""))
	if prev != "" and bool(_snap.get("show_previous", false)):
		var a := 0.55
		if phase == "await" and not reduced:
			a = 0.35 + 0.2 * (0.5 + 0.5 * sin(_now * 3.0))
		var pr := Rect2(Vector2(r.position.x - 76.0, r.position.y + 28.0), Vector2(40, 40))
		draw_rect(pr.grow(3.0), Color(0.1, 0.09, 0.15, a))
		draw_rect(pr, Color(0.96, 0.95, 0.9, a))
		draw_texture_rect(CloakroomArt.symbol_texture(prev), pr, false, Color(1, 1, 1, a + 0.15))
		draw_colored_polygon(PackedVector2Array([Vector2(r.position.x - 28, r.position.y + 40), Vector2(r.position.x - 12, r.position.y + 49), Vector2(r.position.x - 28, r.position.y + 58)]), Color(1, 1, 1, a))
	# the answer's feedback: a tick or a cross on the tag
	if phase == "process" and fb >= 0.0 and fb < FEEDBACK_S:
		var al := 1.0 if reduced else clampf((FEEDBACK_S - fb) / 0.4, 0.0, 1.0)
		var pop := 1.0 if reduced else minf(0.6 + fb / 0.12 * 0.4, 1.0)
		_mark(r.get_center() + Vector2(24, 24), bool(last.get("correct", true)), 26.0 * pop, al)
	if phase == "demo" and str(_snap.get("demo_answer", "")) != "":
		_mark(r.get_center() + Vector2(24, 24), true, 24.0, 1.0)


func _feedback_age() -> float:
	var last: Dictionary = _snap.get("last", {})
	if last.is_empty() or str(_snap.get("phase", "")) != "process":
		return -1.0
	return _now - float(last.get("t", -100.0))


func _mark(c: Vector2, good: bool, s: float, a: float) -> void:
	var ink := Color(0.1, 0.09, 0.15, a)
	if good:
		var pts := PackedVector2Array([c + Vector2(-s * 0.5, 0), c + Vector2(-s * 0.12, s * 0.38), c + Vector2(s * 0.5, -s * 0.42)])
		draw_circle(c, s * 0.78, ink)
		draw_circle(c, s * 0.68, Color(0.25, 0.8, 0.45, a))
		draw_polyline(pts, Color(1, 1, 1, a), maxf(s * 0.16, 3.0))
	else:
		draw_circle(c, s * 0.78, ink)
		draw_circle(c, s * 0.68, Color(0.9, 0.25, 0.25, a))
		var d := s * 0.34
		draw_line(c + Vector2(-d, -d), c + Vector2(d, d), Color(1, 1, 1, a), maxf(s * 0.16, 3.0))
		draw_line(c + Vector2(-d, d), c + Vector2(d, -d), Color(1, 1, 1, a), maxf(s * 0.16, 3.0))


func _lamp(phase: String) -> void:
	var c := Vector2(TAG.get_center().x, 34.0)
	var col := Color("ffb23f")
	var glow := 0.25
	if phase in ["payoff", "done"]:
		col = Color("3fe89a")
		glow = 0.5 + (0.0 if reduced else 0.25 * sin(_now * 8.0))
	elif phase == "process" and not bool((_snap.get("last", {}) as Dictionary).get("correct", true)) and _feedback_age() < 0.6:
		col = Color("e8503a")
		glow = 0.45
	draw_circle(c, 15.0, Color(col.r, col.g, col.b, glow * 0.5))
	draw_circle(c, 9.0, Color("1a1626"))
	draw_circle(c, 7.0, col)
	draw_circle(c + Vector2(-2, -2), 2.0, col.lightened(0.5))


# --- the customer at the counter ------------------------------------------------------------------------------------------------------

func _customer(phase: String) -> void:
	if phase in ["payoff", "done"]:
		return
	var custs: Array = _look.get("customers", [])
	if custs.is_empty():
		return
	var who: Dictionary = custs[int(_snap.get("customer", 0)) % custs.size()]
	var mood := str(_snap.get("reaction", "waiting"))
	var x := 490.0
	var age := _now - float(_snap.get("phase_t0", 0.0))
	if phase == "await" and int(_snap.get("answered", 0)) > 0 and age < WALK_IN_S and not reduced:
		x += (1.0 - age / WALK_IN_S) * 70.0
	var holding := phase != "process" or _handover() < 0.35
	_person(Vector2(x, 200), 1.0, who, mood, holding, _now, true)
	if phase == "process":
		var h := _handover()
		if h > 0.0:  # the coat crosses the counter to the attendant
			var from := Vector2(x - 20.0, 150.0)
			var to := Vector2(284, 128)
			var p := from.lerp(to, minf(h, 1.0))
			p.y -= sin(minf(h, 1.0) * PI) * 22.0
			var correct := bool((_snap.get("last", {}) as Dictionary).get("correct", true))
			var wob := Vector2.ZERO if correct or reduced else Vector2(sin(_now * 22.0) * 2.0, 0)
			_coat(p + wob, Color("e8503a") if int(_snap.get("customer", 0)) % 2 == 0 else Color("3fa0ff"), 0.9)
	elif holding and phase in ["await", "reference", "demo"]:
		_coat(Vector2(x - 24, 124), Color("e8503a") if int(_snap.get("customer", 0)) % 2 == 0 else Color("3fa0ff"), 0.9)


## 0..1 progress of the handover across the process time (0 outside it): a quick answer is a quick swing, a slow one lingers.
func _handover() -> float:
	if str(_snap.get("phase", "")) != "process":
		return 0.0
	var t0 := float(_snap.get("phase_t0", 0.0))
	var span := maxf(float(_snap.get("phase_end", t0 + 1.0)) - t0, 0.1)
	var age := _now - t0
	if span > 1.5:  # (slow: the attendant fumbles about, the coat leaves late)
		return clampf((age - 1.0) / (span - 1.0), 0.0, 1.0)
	return clampf(age / (span * 0.8), 0.0, 1.0)


## A little person standing with their feet at `foot` (design pixels), `k` scale, `mood` waiting | happy | impatient, facing left or right.
func _person(foot: Vector2, k: float, who: Dictionary, mood: String, holding: bool, t: float, face_left: bool, wave := false, silhouette := false) -> void:
	var ink := Color("1a1626")
	var body: Color = who.get("body", Color("888888"))
	var skin: Color = who.get("skin", Color("dddddd"))
	var extra: Color = who.get("extra", Color.WHITE)
	var kind := str(who.get("kind", "alien"))
	var dir := -1.0 if face_left else 1.0
	var bob := 0.0
	if not reduced:
		if mood == "happy":
			bob = -absf(sin(t * 9.0)) * 4.0 * k
		elif mood == "impatient":
			bob = absf(sin(t * 7.0)) * -1.5 * k
		else:
			bob = sin(t * 2.0 + foot.x) * 0.8 * k
	var f := foot + Vector2(0, bob)
	var tap_foot := 0.0 if reduced or mood != "impatient" else maxf(sin(t * 12.0), 0.0) * 3.0 * k
	# legs
	draw_rect(Rect2(f + Vector2(-9, -20 - 0) * k, Vector2(6, 20) * k).grow(1.0), ink)
	draw_rect(Rect2(f + Vector2(3, -20) * k, Vector2(6, 20 - tap_foot / k) * k).grow(1.0), ink)
	draw_rect(Rect2(f + Vector2(-9, -20) * k, Vector2(6, 20) * k), body.darkened(0.45))
	draw_rect(Rect2(f + Vector2(3, -20) * k, Vector2(6, 20 - tap_foot / k) * k), body.darkened(0.45))
	# torso
	var tr := Rect2(f + Vector2(-12, -46) * k, Vector2(24, 28) * k)
	if kind == "wizard" or kind == "fairy":  # (a robe or a dress down to the shins)
		draw_colored_polygon(PackedVector2Array([tr.position + Vector2(2, 0) * k, tr.position + Vector2(22, 0) * k, tr.position + Vector2(28, 36) * k, tr.position + Vector2(-4, 36) * k]), ink)
		draw_colored_polygon(PackedVector2Array([tr.position + Vector2(3, 1) * k, tr.position + Vector2(21, 1) * k, tr.position + Vector2(26, 34) * k, tr.position + Vector2(-2, 34) * k]), body)
	else:
		draw_rect(tr.grow(1.5 * k), ink)
		draw_rect(tr, body)
	if kind == "commuter" or kind == "cyclist":
		draw_rect(Rect2(f + Vector2(-2, -44) * k, Vector2(4, 24) * k), extra)  # (a tie / a stripe)
	# arms
	var sh := f + Vector2(0, -42) * k
	var arm_l := Vector2(-4, 20)  # hand offset from the shoulder, front arm / back arm
	var arm_r := Vector2(4, 20)
	if mood == "happy" or wave:
		var w := 0.0 if reduced else sin(t * 10.0) * 5.0
		arm_l = Vector2(-14, -16 + w)
		arm_r = Vector2(14, -16 - w) if wave else Vector2(14, -16)
	elif mood == "impatient":
		arm_l = Vector2(-14 * dir * -1.0, 8)
		arm_r = Vector2(14 * dir * -1.0, 8)
	if holding:
		arm_l = Vector2(14 * dir, 2)
	for hnd: Vector2 in [arm_l, arm_r]:
		draw_line(sh + Vector2(sign(hnd.x) * 10.0, 0) * k, sh + hnd * k + Vector2(sign(hnd.x) * 6.0, 0) * k, ink, 5.0 * k)
		draw_line(sh + Vector2(sign(hnd.x) * 10.0, 0) * k, sh + hnd * k + Vector2(sign(hnd.x) * 6.0, 0) * k, skin if kind != "alien" else skin.darkened(0.1), 3.0 * k)
	# head
	var hc := f + Vector2(0, -58) * k
	var hr := 13.0 * k
	match kind:
		"dino":
			draw_colored_polygon(PackedVector2Array([f + Vector2(-12 * -dir, -30) * k, f + Vector2(-30 * -dir, -14) * k, f + Vector2(-12 * -dir, -22) * k]), body)  # tail
			draw_circle(hc, hr + 1.5 * k, ink)
			draw_circle(hc, hr, skin)
			draw_rect(Rect2(hc + Vector2(dir * 6.0 - 6.0, 2) * k, Vector2(12, 8) * k), skin)  # snout
			for sp in 3:
				draw_colored_polygon(PackedVector2Array([hc + Vector2(-5 + sp * 5, -hr / k - 5) * k, hc + Vector2(-1 + sp * 5, -hr / k + 1) * k, hc + Vector2(-9 + sp * 5, -hr / k + 1) * k]), extra)
		"wizard":
			draw_circle(hc, hr + 1.5 * k, ink)
			draw_circle(hc, hr, skin)
			draw_colored_polygon(PackedVector2Array([hc + Vector2(-17, -6) * k, hc + Vector2(17, -6) * k, hc + Vector2(3, -34) * k]), ink)
			draw_colored_polygon(PackedVector2Array([hc + Vector2(-15, -7) * k, hc + Vector2(15, -7) * k, hc + Vector2(3, -31) * k]), body.lightened(0.1))
			draw_circle(hc + Vector2(0, -16) * k, 2.5 * k, extra)
		"fairy":
			for sx in [-1.0, 1.0]:
				draw_circle(f + Vector2(sx * 16.0, -40) * k, 9.0 * k, Color(extra.r, extra.g, extra.b, 0.7))
			draw_circle(hc, hr + 1.5 * k, ink)
			draw_circle(hc, hr, skin)
			draw_circle(hc + Vector2(0, -12) * k, 5.0 * k, extra)
		"alien":
			for sx in [-1.0, 1.0]:
				draw_line(hc + Vector2(sx * 5.0, -10) * k, hc + Vector2(sx * 10.0, -24) * k, ink, 2.0 * k)
				draw_circle(hc + Vector2(sx * 10.0, -24) * k, 3.0 * k, extra)
			draw_circle(hc, hr + 1.5 * k, ink)
			draw_circle(hc, hr, skin)
		"cyclist":
			draw_circle(hc, hr + 1.5 * k, ink)
			draw_circle(hc, hr, skin)
			draw_colored_polygon(PackedVector2Array([hc + Vector2(-14, -2) * k, hc + Vector2(14, -2) * k, hc + Vector2(10, -14) * k, hc + Vector2(-10, -14) * k]), extra)
		_:  # commuter
			draw_circle(hc, hr + 1.5 * k, ink)
			draw_circle(hc, hr, skin)
			draw_rect(Rect2(hc + Vector2(-13, -14) * k, Vector2(26, 8) * k), extra)
			draw_rect(Rect2(hc + Vector2(dir * 6.0 - 3.0, -8) * k, Vector2(12, 3) * k), extra.darkened(0.3))
	if silhouette:
		return
	# the face: two eyes, a mouth for the mood
	var ey := hc + Vector2(0, -2) * k
	var eyes := 4.0 if kind == "alien" else 2.2
	for sx in [-1.0, 1.0]:
		draw_circle(ey + Vector2(sx * 5.0 + dir * 1.5, 0) * k, eyes * k, ink)
	var m := hc + Vector2(dir * 1.5, 6) * k
	match mood:
		"happy":
			draw_polyline(PackedVector2Array([m + Vector2(-5, -1) * k, m + Vector2(-2, 2) * k, m + Vector2(2, 2) * k, m + Vector2(5, -1) * k]), ink, 1.6 * k)
		"impatient":
			draw_polyline(PackedVector2Array([m + Vector2(-5, 2) * k, m + Vector2(-2, -1) * k, m + Vector2(2, -1) * k, m + Vector2(5, 2) * k]), ink, 1.6 * k)
			draw_line(ey + Vector2(-9, -5) * k, ey + Vector2(-2, -3) * k, ink, 1.8 * k)  # (a frown's brows)
			draw_line(ey + Vector2(9, -5) * k, ey + Vector2(2, -3) * k, ink, 1.8 * k)
			if not reduced and sin(t * 5.0) > 0.0:
				draw_circle(hc + Vector2(-15 * dir, -10) * k, 2.0 * k, Color("e8503a"))  # (a flash of temper)
		_:
			draw_line(m + Vector2(-4, 0) * k, m + Vector2(4, 0) * k, ink, 1.6 * k)


# --- the small things: the door, the control hints, the payoff ----------------------------------------------------------------------

func _door() -> void:
	draw_rect(DOOR.grow(2.0), Color("1a1626"))
	draw_rect(DOOR, Color("c9a86a"))
	draw_rect(DOOR.grow(-5.0), Color("5a4630"))
	draw_circle(DOOR.position + Vector2(20, 18), 2.0, Color("ffd93d"))
	draw_colored_polygon(PackedVector2Array([DOOR.position + Vector2(30, 6), DOOR.position + Vector2(44, 17), DOOR.position + Vector2(30, 28)]), Color(1, 1, 1, 0.8))


## The two answers as pictograms at the foot of the stage, faint; in the demonstration the right one is lit.
func _hints(phase: String) -> void:
	var ans := str(_snap.get("demo_answer", "")) if phase == "demo" else ""
	var pulse := 1.0 if reduced else 0.75 + 0.25 * sin(_now * 8.0)
	for side in 2:
		var id := "same" if side == 0 else "different"
		var r := Rect2(Vector2(160.0 if side == 0 else 436.0, 205.0), Vector2(44, 22))
		var lit := ans == id
		if phase == "demo" or lit:
			draw_rect(r.grow(3.0), Color(1, 1, 1, (0.9 * pulse) if lit else 0.12))
			draw_rect(r, Color(0.1, 0.1, 0.16, 0.95))
			CloakroomArt.draw_pictogram(self, r.grow(-2.0), id, 1.0 if lit else 0.4)


func _sparkles() -> void:
	var age := _now - float(_snap.get("phase_t0", 0.0))
	for k in 14:
		var ph := float(k) * 2.399
		var life := fmod(age * 0.9 + float(k) * 0.13, 1.0)
		var p := Vector2(150.0 + fmod(float(k) * 97.0, 340.0), 150.0 - life * 130.0)
		var col := [Color("ffd93d"), Color("3fe89a"), Color("ff8fe0"), Color("5ec8f2")][k % 4] as Color
		draw_rect(Rect2(p + Vector2(sin(ph + age * 3.0) * 8.0, 0), Vector2(4, 4)), Color(col.r, col.g, col.b, 1.0 - life))
