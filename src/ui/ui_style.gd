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


# --- unit icons and cards ------------------------------------------------------------------------------------------

const ROSTER_PATH := "res://data/rosters/openra_mvp_01.json"
const PLAYER_COLOUR := Color(0.35, 0.62, 1.0)  # the blue the battle view gives side 0 (BattleView.FACTION_BASE[0])
const VEHICLES := ["jeep", "apc", "1tnk", "2tnk", "arty", "ftrk"]  # rewards that need a war factory
const ICON_HEIGHT := 44.0  # icons are scaled by whole pixels towards this height (soldiers come out at 2x)
const MAX_ICONS := 6

static var _bank: SpriteBank
static var _material: ShaderMaterial
static var _roles: Dictionary = {}
static var _crops: Dictionary = {}  # image -> Rect2i of its visible pixels


## The shared sprite bank for menu icons (loaded once).
static func bank() -> SpriteBank:
	if _bank == null:
		_bank = SpriteBank.new()
		_bank.load()
	return _bank


## The player-colour remap material (the battle view's: the sprite's remap pixels recoloured to the blue ramp).
static func player_material() -> ShaderMaterial:
	if _material != null:
		return _material
	var b := bank()
	var src := PackedVector3Array()
	for c in b.remap_ramp:
		src.append(Vector3(float(c[0]) / 255.0, float(c[1]) / 255.0, float(c[2]) / 255.0))
	while src.size() < 16:
		src.append(Vector3.ZERO)
	var top := src[0].length() if src.size() > 0 else 1.0
	var dst := PackedVector3Array()
	for i in 16:
		var k: float = src[i].length() / top
		var v := Vector3(PLAYER_COLOUR.r, PLAYER_COLOUR.g, PLAYER_COLOUR.b) * k
		dst.append(Vector3(clampf(v.x, 0.0, 1.0), clampf(v.y, 0.0, 1.0), clampf(v.z, 0.0, 1.0)))
	var mat := ShaderMaterial.new()
	mat.shader = load("res://src/ui/faction_remap.gdshader") as Shader
	mat.set_shader_parameter("src_ramp", src)
	mat.set_shader_parameter("dst_ramp", dst)
	_material = mat
	return _material


## The sprite image of a building role in the roster (pillbox -> pbox, turret -> gun, flame -> ftur).
static func building_image(role: String) -> String:
	if _roles.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ROSTER_PATH))
		_roles = parsed.get("roles", {}) if typeof(parsed) == TYPE_DICTIONARY else {}
	return str(_roles.get(role, ""))


## What a sound's instrument produces, one entry per step of its reward cycle (at most `max_icons`):
## {actor, count} for a unit (count is the squad size, 1 for a single unit), {building, count: 1} for a defense and
## {repair: true, count: 1} for a repair crew.
static func reward_icons(index: LibraryIndex, sound: String, max_icons: int = MAX_ICONS) -> Array:
	var out: Array = []
	for id in Loadout.reward_cycle(index, sound):
		if out.size() >= max_icons:
			break
		var r: Dictionary = MissionRules.reward(str(id))
		match str(r.get("type", "repair")):
			"unit":
				out.append({"actor": str(r.get("actor", id)), "count": maxi(int(r.get("count", 1)), 1)})
			"build":
				out.append({"building": building_image(str(r.get("role", ""))), "count": 1})
			_:
				out.append({"repair": true, "count": 1})
	return out


## `icons` with the vehicles turned into repair crews (a mission without a war factory builds none).
static func without_vehicles(icons: Array) -> Array:
	var out: Array = []
	for ic: Dictionary in icons:
		out.append({"repair": true, "count": 1} if VEHICLES.has(str(ic.get("actor", ""))) else ic)
	return out


## The visible part of an actor's first frame, so a 50x39 canvas around a soldier does not waste the card width.
static func _crop(image: String, tex: Texture2D) -> Rect2i:
	if _crops.has(image):
		return _crops[image]
	var img := tex.get_image()
	var r := Rect2i(Vector2i.ZERO, Vector2i(tex.get_width(), tex.get_height()))
	if img != null:
		var used := img.get_used_rect()
		if used.size.x > 0 and used.size.y > 0:
			r = used
	_crops[image] = r
	return r


## One icon: the actor frame in the player colour, nearest-filtered and scaled by whole pixels (soldiers 2x), with a
## small "x3" beside it for a squad; a glyph for a repair crew. `icon` is an entry of reward_icons.
static func unit_icon(icon: Dictionary) -> Control:
	var box := HBoxContainer.new()
	box.add_theme_constant_override("separation", 3)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if bool(icon.get("repair", false)):
		var g := Label.new()
		g.text = "⚒"
		g.add_theme_font_size_override("font_size", 30)
		g.add_theme_color_override("font_color", GOOD)
		g.custom_minimum_size = Vector2(34, ICON_HEIGHT)
		g.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		g.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		g.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(g)
		return box
	var image := str(icon.get("actor", icon.get("building", "")))
	var b := bank()
	var seq := "idle"
	if b.has_sequence(image, "stand"):
		seq = "stand"  # a soldier stands
	elif icon.has("building") and b.has_sequence(image, "turret"):
		seq = "turret"  # a gun turret shows its turret (its idle frame is the empty start of the build-up)
	var tex := b.texture_for(image, seq, PI * 0.5 if seq != "idle" else 0.0, 0)
	if tex != null:
		var crop := _crop(image, tex)
		var atlas := AtlasTexture.new()
		atlas.atlas = tex
		atlas.region = Rect2(crop)
		var s := clampi(int(ICON_HEIGHT / float(maxi(crop.size.y, 1))), 1, 3)
		var rect := TextureRect.new()
		rect.texture = atlas
		rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		rect.material = player_material()
		rect.stretch_mode = TextureRect.STRETCH_SCALE
		rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		rect.custom_minimum_size = Vector2(crop.size * s)
		rect.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(rect)
	else:
		var q := note("?", MUTED, 20)
		q.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(q)
	if int(icon.get("count", 1)) > 1:
		var n := note("x%d" % int(icon["count"]), MUTED, 14)
		n.autowrap_mode = TextServer.AUTOWRAP_OFF
		n.size_flags_vertical = Control.SIZE_SHRINK_END
		n.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(n)
	return box


## A horizontal strip of unit_icon()s.
static func icon_strip(icons: Array) -> HBoxContainer:
	var strip := HBoxContainer.new()
	strip.add_theme_constant_override("separation", 10)
	strip.custom_minimum_size = Vector2(0, ICON_HEIGHT + 4)
	strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for ic: Dictionary in icons:
		strip.add_child(unit_icon(ic))
	return strip


## A selectable card for one library item (an entry of the Loadout screen row_items: {id, name, key, meta, locked,
## lock_text, equipped, icons, blurb, listenable}). Returns {root, button, listen}: `button` is the toggle behind the
## contents (equipped = pressed, locked = disabled), `listen` the small Listen button (null when there is nothing to
## audition). The caller connects `button.pressed` and `listen.pressed`.
static func card(item: Dictionary, width: float = 260.0) -> Dictionary:
	var root := MarginContainer.new()
	root.custom_minimum_size = Vector2(width, 92)
	var button := Button.new()
	button.toggle_mode = true
	button.button_pressed = bool(item.get("equipped", false))
	button.disabled = bool(item.get("locked", false))
	root.add_child(button)
	var pad := MarginContainer.new()
	pad.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for side in ["left", "right"]:
		pad.add_theme_constant_override("margin_" + side, 14)
	for side in ["top", "bottom"]:
		pad.add_theme_constant_override("margin_" + side, 10)
	root.add_child(pad)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 4)
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pad.add_child(col)
	var locked := bool(item.get("locked", false))
	var inner := Vector2(width - 28, 0)
	var head := Label.new()
	head.text = str(item.get("name", ""))
	head.add_theme_font_size_override("font_size", 21)
	head.add_theme_color_override("font_color", MUTED.darkened(0.2) if locked else TEXT)
	head.custom_minimum_size = inner
	head.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(head)
	var meta := str(item.get("meta", ""))
	if not str(item.get("key", "")).is_empty():
		meta = "%s  ·  %s" % [str(item["key"]), meta] if not meta.is_empty() else str(item["key"])
	if not meta.is_empty():
		var m := note(meta, MUTED, 15)
		m.custom_minimum_size = inner
		m.mouse_filter = Control.MOUSE_FILTER_IGNORE
		col.add_child(m)
	if locked:
		var l := note(str(item.get("lock_text", "Locked")), WARN, 16)
		l.custom_minimum_size = inner
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		col.add_child(l)
	elif not (item.get("icons", []) as Array).is_empty():
		col.add_child(icon_strip(item["icons"]))
	var blurb := str(item.get("blurb", ""))
	if not blurb.is_empty() and not locked:
		var bl := note(blurb, MUTED, 15)
		bl.custom_minimum_size = inner
		bl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		col.add_child(bl)
	var listen: Button = null
	if bool(item.get("listenable", false)) and not locked:
		listen = Button.new()
		listen.text = "Listen"
		listen.custom_minimum_size = Vector2(110, 38)
		listen.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
		listen.add_theme_font_size_override("font_size", 17)
		col.add_child(listen)
	return {"root": root, "button": button, "listen": listen}
