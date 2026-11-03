class_name StoryHud
extends Control
## The play screen's narrative overlay in the neon style: the chapter title card, the act cards, the decision captions and the
## countdown. Everything animates on song time (pausing freezes it; a fast-forward shows what a player would see at that moment),
## keeps to the top-left corner and the centre so it never covers the pads or the falling notes' landing zone, and never flashes.

const ACT_HOLD := 3.6
const TOAST_HOLD := 4.6
const IN_S := 0.35
const OUT_S := 0.6
const CYAN := Color(0.35, 0.92, 1.0)
const MAGENTA := Color(1.0, 0.35, 0.78)
const AMBER := Color(1.0, 0.78, 0.4)
const INK := Color(0.02, 0.0, 0.1)

var title := ""
var subtitle := ""
var title_until := 2.2  # song seconds: the title card is gone by then
var reduced := false
var t_now := -2.0
var countdown := ""  # the count-in digit ("" when none)
var countdown_frac := 0.0  # 0..1 through the current digit
var _act := {}  # {kicker, text, t0}
var _toast := {}  # {text, tone, t0, hold}
var _font: Font
var _box := StyleBoxFlat.new()


func _ready() -> void:
	_font = ThemeDB.fallback_font
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func show_act(kicker: String, text: String, t0: float) -> void:
	_act = {"kicker": kicker, "text": text, "t0": t0}


## tone: "good" (cyan), "bad" (amber) or "end" (the ending's title, magenta, held to the end).
func show_toast(text: String, tone: String, t0: float, hold := TOAST_HOLD) -> void:
	_toast = {"text": text, "tone": tone, "t0": t0, "hold": hold}


func set_time(t: float) -> void:
	t_now = t
	queue_redraw()


## 0..1 visibility of a card shown at t0 for `hold` seconds (eased in, held, faded out).
func _vis(t0: float, hold: float) -> float:
	var age := t_now - t0
	if age < 0.0 or age > hold + OUT_S:
		return 0.0
	if age < IN_S:
		var u := age / IN_S
		return u * u * (3.0 - 2.0 * u)
	if age > hold:
		return 1.0 - (age - hold) / OUT_S
	return 1.0


func _panel(r: Rect2, accent: Color, a: float) -> void:
	_box.bg_color = Color(0.03, 0.02, 0.1, 0.72 * a)
	_box.border_color = Color(accent, 0.55 * a)
	_box.set_border_width_all(0)
	_box.border_width_left = 4
	_box.set_corner_radius_all(6)
	_box.shadow_color = Color(accent, 0.18 * a)
	_box.shadow_size = 10
	draw_style_box(_box, r)


func _text(pos: Vector2, s: String, fs: int, col: Color, outline := 6, align := HORIZONTAL_ALIGNMENT_LEFT, width := -1.0) -> void:
	draw_string_outline(_font, pos, s, align, width, fs, outline, Color(INK, col.a * 0.9))
	draw_string(_font, pos, s, align, width, fs, col)


func _draw() -> void:
	var w := size.x
	var k := clampf(size.y / 720.0, 0.75, 1.6)  # type scales with the screen height
	# the chapter title card
	if t_now < title_until + OUT_S and title != "":
		var a := clampf(1.0 - (t_now - title_until) / OUT_S, 0.0, 1.0) if t_now > title_until else 1.0
		var grow := 0.0 if reduced else clampf((t_now + 2.0) / 4.0, 0.0, 1.0) * 0.06
		var fs := int(84 * k * (1.0 + grow))
		var y := size.y * 0.24
		draw_rect(Rect2(0, y - fs * 1.05, w, fs * 1.75), Color(0.02, 0.0, 0.08, 0.45 * a))
		draw_line(Vector2(w * 0.2, y - fs * 1.05), Vector2(w * 0.8, y - fs * 1.05), Color(MAGENTA, 0.7 * a), 2.0)
		draw_line(Vector2(w * 0.2, y + fs * 0.7), Vector2(w * 0.8, y + fs * 0.7), Color(CYAN, 0.7 * a), 2.0)
		_text(Vector2(0, y), title, fs, Color(1.0, 0.92, 1.0, a), 14, HORIZONTAL_ALIGNMENT_CENTER, w)
		if subtitle != "":
			_text(Vector2(0, y + fs * 0.5), subtitle, int(22 * k), Color(CYAN.lightened(0.4), a), 6, HORIZONTAL_ALIGNMENT_CENTER, w)
	var x := 22.0 * k
	var y0 := 18.0 * k
	# the act card: a kicker ("ACT II") over the act's title, sliding in from the left
	if not _act.is_empty():
		var a := _vis(float(_act["t0"]), ACT_HOLD)
		if a > 0.0:
			var slide := 0.0 if reduced else (1.0 - a) * -40.0 * k
			var fs := int(30 * k)
			var tw := _font.get_string_size(str(_act["text"]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			var r := Rect2(x + slide - 10.0 * k, y0, maxf(tw, 160.0 * k) + 36.0 * k, fs * 2.25)
			_panel(r, MAGENTA, a)
			_text(Vector2(r.position.x + 18.0 * k, y0 + fs * 0.8), str(_act["kicker"]), int(17 * k), Color(MAGENTA.lightened(0.3), a), 4)
			_text(Vector2(r.position.x + 18.0 * k, y0 + fs * 1.85), str(_act["text"]), fs, Color(1, 1, 1, a), 7)
			y0 = r.end.y + 10.0 * k
	# the decision caption under it
	if not _toast.is_empty():
		var a := _vis(float(_toast["t0"]), float(_toast["hold"]))
		if a > 0.0:
			var tone := str(_toast["tone"])
			var col: Color = {"good": CYAN, "bad": AMBER, "end": MAGENTA}.get(tone, CYAN)
			var fs := int((34 if tone == "end" else 24) * k)
			var tw := _font.get_string_size(str(_toast["text"]), HORIZONTAL_ALIGNMENT_LEFT, -1, fs).x
			var slide := 0.0 if reduced else (1.0 - a) * -30.0 * k
			var r := Rect2(x + slide - 10.0 * k, y0, tw + 40.0 * k, fs * 1.75)
			_panel(r, col, a)
			_text(Vector2(r.position.x + 20.0 * k, r.position.y + fs * 1.18), str(_toast["text"]), fs, Color(col.lightened(0.55), a), 7)
	# the count-in
	if countdown != "":
		var c := Vector2(w * 0.5, size.y * 0.3)
		var rr := 70.0 * k
		draw_circle(c, rr, Color(0.02, 0.0, 0.1, 0.55))
		draw_arc(c, rr, -PI * 0.5, -PI * 0.5 + TAU * (1.0 - countdown_frac), 64, Color(CYAN, 0.9), 5.0 * k, true)
		var pop := 1.0 if reduced else 1.0 + 0.25 * maxf(0.0, 1.0 - countdown_frac / 0.15)
		draw_set_transform(c, 0.0, Vector2(pop, pop))
		var fs := int(96 * k)
		_text(Vector2(-rr, fs * 0.35), countdown, fs, Color.WHITE, 12, HORIZONTAL_ALIGNMENT_CENTER, rr * 2.0)
		draw_set_transform_matrix(Transform2D.IDENTITY)
