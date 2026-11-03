class_name StoryStyle
extends RefCounted
## The Story Campaign's own look for its menus and overlays: the club's neon palette (indigo shadows, magenta and cyan light, an
## amber accent) instead of the military campaign's steel and brass. A Theme with neon button states, glowing panels, titles with a
## soft neon outline, and a backdrop (gradient, perspective floor grid, light haze) for full screens. Other modes keep UiStyle.

const BG_TOP := Color(0.06, 0.03, 0.16)
const BG_BOTTOM := Color(0.01, 0.01, 0.05)
const PANEL := Color(0.06, 0.04, 0.15, 0.9)
const EDGE := Color(0.42, 0.3, 0.95)
const CYAN := Color(0.3, 0.9, 1.0)
const MAGENTA := Color(1.0, 0.3, 0.75)
const AMBER := Color(1.0, 0.78, 0.38)
const TEXT := Color(0.95, 0.93, 1.0)
const MUTED := Color(0.68, 0.66, 0.88)
const GOOD := Color(0.45, 1.0, 0.8)
const WARN := Color(1.0, 0.72, 0.45)
const GAP := 14

static var _theme: Theme


static func theme() -> Theme:
	if _theme != null:
		return _theme
	var t := Theme.new()
	t.default_font_size = 22
	var states := {
		"normal": [Color(0.09, 0.06, 0.2, 0.92), EDGE.darkened(0.15), 0.0],
		"hover": [Color(0.14, 0.08, 0.3, 0.95), CYAN, 0.25],
		"pressed": [Color(0.32, 0.08, 0.32, 0.95), MAGENTA, 0.35],
		"focus": [Color(0, 0, 0, 0), CYAN, 0.35],
		"disabled": [Color(0.05, 0.04, 0.1, 0.8), EDGE.darkened(0.6), 0.0],
	}
	for state in states:
		var sb := StyleBoxFlat.new()
		sb.bg_color = states[state][0]
		sb.border_color = states[state][1]
		sb.set_border_width_all(3 if state == "focus" else 2)
		sb.set_corner_radius_all(10)
		sb.content_margin_left = 20
		sb.content_margin_right = 20
		sb.content_margin_top = 8
		sb.content_margin_bottom = 8
		sb.draw_center = state != "focus"
		if float(states[state][2]) > 0.0:
			sb.shadow_color = Color(states[state][1], float(states[state][2]))
			sb.shadow_size = 10
		t.set_stylebox(state, "Button", sb)
	t.set_color("font_color", "Button", TEXT)
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", Color.WHITE)
	t.set_color("font_focus_color", "Button", Color.WHITE)
	t.set_color("font_disabled_color", "Button", MUTED.darkened(0.4))
	t.set_color("font_outline_color", "Button", Color(0.02, 0.0, 0.1))
	t.set_constant("outline_size", "Button", 4)
	t.set_color("font_color", "Label", TEXT)
	t.set_font_size("font_size", "Label", 20)
	t.set_stylebox("panel", "PanelContainer", panel_box())
	var sb_scroll := StyleBoxFlat.new()
	sb_scroll.bg_color = Color(0.3, 0.2, 0.7, 0.35)
	sb_scroll.set_corner_radius_all(4)
	t.set_stylebox("grabber", "VScrollBar", sb_scroll)
	_theme = t
	return t


static func panel_box(accent: Color = EDGE) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = PANEL
	sb.border_color = Color(accent, 0.85)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(14)
	sb.shadow_color = Color(accent, 0.22)
	sb.shadow_size = 14
	sb.content_margin_left = 26
	sb.content_margin_right = 26
	sb.content_margin_top = 18
	sb.content_margin_bottom = 18
	return sb


static func title(text: String, font_size: int = 34, color: Color = TEXT, glow: Color = MAGENTA) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.add_theme_color_override("font_outline_color", Color(glow, 0.55))
	l.add_theme_constant_override("outline_size", maxi(4, font_size / 6))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


static func note(text: String, color: Color = MUTED, font_size: int = 18) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## A full screen in the neon style: backdrop, safe-area margins, a header row (optional Back, the title) and a scrolling column.
## Returns {root_box, header, content}.
static func screen(root: Control, title_text: String, back: Callable = Callable()) -> Dictionary:
	root.theme = theme()
	var bg := Backdrop.new()
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(bg)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var safe := UiStyle.safe_margins(root)
	margin.add_theme_constant_override("margin_left", int(safe.x) + 40)
	margin.add_theme_constant_override("margin_right", int(safe.y) + 40)
	margin.add_theme_constant_override("margin_top", 20)
	margin.add_theme_constant_override("margin_bottom", 20)
	root.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", GAP)
	margin.add_child(box)
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", GAP)
	box.add_child(header)
	if back.is_valid():
		header.add_child(UiStyle.button("Back", back, 120, 52))
	var t := title(title_text, 38)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_LEFT
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(t)
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	box.add_child(scroll)
	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", GAP)
	scroll.add_child(content)
	return {"root_box": box, "header": header, "content": content}


## The menus' backdrop: a dark indigo gradient, a neon horizon and a perspective floor grid, with two soft light pools that drift
## slowly (wall-clock driven: menus have no song).
class Backdrop:
	extends Control

	func _process(_delta: float) -> void:
		queue_redraw()

	func _draw() -> void:
		var w := size.x
		var h := size.y
		var steps := 24
		for i in steps:
			var u := float(i) / float(steps)
			draw_rect(Rect2(0, h * u, w, h / float(steps) + 1.0), BG_TOP.lerp(BG_BOTTOM, u))
		var t := float(Time.get_ticks_msec()) / 1000.0
		var hy := h * 0.58
		for k in 2:  # drifting light pools
			var c := Vector2(w * (0.3 + 0.4 * k) + sin(t * 0.21 + k * 2.0) * w * 0.12, hy - h * 0.12)
			var col: Color = MAGENTA if k == 0 else CYAN
			for r in 6:
				draw_circle(c, h * (0.32 - 0.05 * r), Color(col, 0.018 + 0.01 * r))
		draw_line(Vector2(0, hy), Vector2(w, hy), Color(MAGENTA, 0.55), 2.0)
		draw_line(Vector2(0, hy + 3.0), Vector2(w, hy + 3.0), Color(MAGENTA, 0.15), 6.0)
		var vp := Vector2(w * 0.5, hy - h * 0.25)
		for k in range(-12, 13):  # floor lines converging on the vanishing point
			var x := w * 0.5 + float(k) * w * 0.09
			var dir := Vector2(x, hy) - vp
			draw_line(Vector2(x, hy), Vector2(x, hy) + dir * ((h - hy) / maxf(dir.y, 1.0)), Color(EDGE, 0.16), 1.5)
		var scroll := fposmod(t * 0.15, 1.0)
		for k in 9:  # floor rows sliding toward the viewer
			var d := float(k) + 1.0 - scroll  # depth: 1 at the bottom edge, larger towards the horizon
			var y := hy + (h - hy) * 0.95 / d
			if y > hy and y < h:
				draw_line(Vector2(0, y), Vector2(w, y), Color(EDGE, 0.06 + 0.2 / d), 1.5)
