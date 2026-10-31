class_name UiStyle
extends RefCounted
## The menus' one look (OpenRA-like: dark steel panels, brass accents, plain type): colours, a shared Theme with
## normal / hover / pressed / focused / disabled states, and small builders so every screen spaces and sizes alike.
## Screens lay themselves out inside the display's safe area.

const BG := Color(0.07, 0.08, 0.10)
const PANEL := Color(0.13, 0.14, 0.17)
const PANEL_EDGE := Color(0.32, 0.34, 0.38)
const ACCENT := Color(0.88, 0.72, 0.36)
const TEXT := Color(0.93, 0.93, 0.9)
const MUTED := Color(0.64, 0.67, 0.72)
const GOOD := Color(0.62, 0.92, 0.62)
const WARN := Color(1.0, 0.68, 0.5)
const GAP := 14

static var _theme: Theme


static func theme() -> Theme:
	if _theme != null:
		return _theme
	var t := Theme.new()
	t.default_font_size = 22
	var states := {
		"normal": [PANEL.lightened(0.04), PANEL_EDGE],
		"hover": [PANEL.lightened(0.12), ACCENT.darkened(0.2)],
		"pressed": [ACCENT.darkened(0.55), ACCENT],
		"focus": [Color(0, 0, 0, 0), ACCENT],
		"disabled": [PANEL.darkened(0.3), PANEL_EDGE.darkened(0.4)],
	}
	for state in states:
		var sb := StyleBoxFlat.new()
		sb.bg_color = states[state][0]
		sb.border_color = states[state][1]
		sb.set_border_width_all(3 if state == "focus" else 2)
		sb.set_corner_radius_all(6)
		sb.content_margin_left = 18
		sb.content_margin_right = 18
		sb.content_margin_top = 8
		sb.content_margin_bottom = 8
		sb.draw_center = state != "focus"
		t.set_stylebox(state, "Button", sb)
	t.set_color("font_color", "Button", TEXT)
	t.set_color("font_hover_color", "Button", Color.WHITE)
	t.set_color("font_pressed_color", "Button", Color.WHITE)
	t.set_color("font_focus_color", "Button", Color.WHITE)
	t.set_color("font_disabled_color", "Button", MUTED.darkened(0.3))
	t.set_color("font_color", "Label", TEXT)
	t.set_font_size("font_size", "Label", 20)
	t.set_stylebox("panel", "PanelContainer", panel_box())
	var grab := StyleBoxFlat.new()
	grab.bg_color = ACCENT
	grab.set_corner_radius_all(10)
	t.set_stylebox("grabber_area", "HSlider", grab)
	t.set_stylebox("grabber_area_highlight", "HSlider", grab)
	var rail := StyleBoxFlat.new()
	rail.bg_color = PANEL.lightened(0.15)
	rail.set_corner_radius_all(4)
	rail.content_margin_top = 4
	rail.content_margin_bottom = 4
	t.set_stylebox("slider", "HSlider", rail)
	_theme = t
	return t


static func panel_box() -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = PANEL
	sb.border_color = PANEL_EDGE
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(8)
	sb.content_margin_left = 24
	sb.content_margin_right = 24
	sb.content_margin_top = 18
	sb.content_margin_bottom = 18
	return sb


## A full screen: background, safe-area margins, a header row (title, optional Back) and a scrolling content column.
## Returns {root_box, header, content}.
static func screen(root: Control, title_text: String, back: Callable = Callable()) -> Dictionary:
	root.theme = theme()
	var bg := ColorRect.new()
	bg.color = BG
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(bg)
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var safe := safe_margins(root)
	margin.add_theme_constant_override("margin_left", int(safe.x) + 32)
	margin.add_theme_constant_override("margin_right", int(safe.y) + 32)
	margin.add_theme_constant_override("margin_top", 18)
	margin.add_theme_constant_override("margin_bottom", 18)
	root.add_child(margin)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", GAP)
	margin.add_child(box)
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", GAP)
	box.add_child(header)
	if back.is_valid():
		var b := button("Back", back, 120, 52)
		header.add_child(b)
	var t := title(title_text, 34)
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


static func safe_margins(node: Control) -> Vector2:
	var safe := DisplayServer.get_display_safe_area()
	var screen_size := DisplayServer.screen_get_size()
	if screen_size.x <= 0 or safe.size.x <= 0 or node.get_viewport() == null:
		return Vector2.ZERO
	var k := node.get_viewport().get_visible_rect().size.x / float(screen_size.x)
	return Vector2(float(safe.position.x) * k, float(screen_size.x - safe.end.x) * k)


static func button(text: String, cb: Callable, min_w: float = 0.0, min_h: float = 60.0) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(min_w, min_h)
	if cb.is_valid():
		b.pressed.connect(cb)
	return b


static func title(text: String, font_size: int = 34) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", ACCENT)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return l


static func note(text: String, color: Color = MUTED, font_size: int = 18) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", font_size)
	l.add_theme_color_override("font_color", color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l
