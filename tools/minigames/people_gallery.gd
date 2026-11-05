extends Control
## Preview of the blackjack people and the player's hands, rendered through a low-res SubViewport exactly like the game (640 x 230 shown nearest-neighbour at twice the size; env
## RW_GALLERY_LOW=1 gives 320 x 115 shown at four times). Pages (env RW_GALLERY_PAGE=n): 1 every mood for each person, 2 every gesture for the dealer, 3 gaze in nine directions,
## 4 to 6 the player's hand gestures at progress 0.2, 0.55 and 0.9. Env RW_GALLERY_T fixes the animation time (seconds) for repeatable screenshots.

const WALL := Color("a8dcc4")
const MARK := Color("ff2fa0")
const CELL_W := 106.0
const CELL_H := 115.0

class Layer:
	extends Control
	var fn: Callable

	func _draw() -> void:
		if fn.is_valid():
			fn.call(self)

class Cell:
	extends Control
	var fn: Callable

	func _init() -> void:
		clip_contents = true

	func _draw() -> void:
		if fn.is_valid():
			fn.call(self)

var _low := false
var _page := 1
var _size := Vector2(640, 230)
var _u := 1.0
var _sub: SubViewport
var _time := 0.0
var _fixed := -1.0
var _layers: Array[Control] = []


func _ready() -> void:
	_low = OS.get_environment("RW_GALLERY_LOW") == "1"
	if OS.has_environment("RW_GALLERY_PAGE"):
		_page = int(OS.get_environment("RW_GALLERY_PAGE"))
	if OS.has_environment("RW_GALLERY_T"):
		_fixed = float(OS.get_environment("RW_GALLERY_T"))
	_size = Vector2(320, 115) if _low else Vector2(640, 230)
	_u = _size.y / 230.0
	_sub = SubViewport.new()
	_sub.size = Vector2i(_size)
	_sub.transparent_bg = false
	_sub.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_sub)
	var rect := TextureRect.new()
	rect.texture = _sub.get_texture()
	rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	rect.stretch_mode = TextureRect.STRETCH_SCALE
	rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(rect)
	var bg := Layer.new()
	bg.size = _size
	bg.fn = func(ci: Control) -> void: ci.draw_rect(Rect2(Vector2.ZERO, _size), WALL)
	_sub.add_child(bg)
	match _page:
		1:
			_page_moods()
		2:
			_page_gestures()
		3:
			_page_gaze()
		_:
			_page_hands(_page - 4)


func _process(delta: float) -> void:
	_time += delta
	for l in _layers:
		l.queue_redraw()


func _now() -> float:
	return _fixed if _fixed >= 0.0 else _time


func _beat() -> float:
	return _now() * 2.9


func _add_layer(pos: Vector2, size: Vector2, fn: Callable, clip := false) -> Control:
	var l: Control = Cell.new() if clip else Layer.new()
	l.position = pos
	l.size = size
	l.set("fn", fn)
	_sub.add_child(l)
	_layers.append(l)
	return l


func _marker(ci: Control, p: Vector2) -> void:
	var u := _u
	ci.draw_rect(Rect2(roundf(p.x - 2.0 * u), roundf(p.y - 2.0 * u), maxf(2.0, 4.0 * u), maxf(2.0, 4.0 * u)), MARK)


func _page_moods() -> void:
	var who := ["dealer", "npc_a", "npc_b"]
	_add_layer(Vector2.ZERO, _size, func(ci: Control) -> void:
		var u := _u
		for r in 3:
			for m in 10:
				var c := Vector2(roundf((32.0 + 64.0 * m) * u), roundf((36.0 + 74.0 * r) * u))
				var f := BlackjackPeople.face_params(BlackjackPeople.MOOD_NAMES[m])
				BlackjackPeople.draw_person(ci, who[r], c, u, f, c + Vector2(0.0, 8.0 * u), "rest", 0.0, _beat()))
	_labels(BlackjackPeople.MOOD_NAMES, 64.0, 32.0, 0.0)


func _label(text: String, pos_canvas: Vector2) -> void:
	var sc := get_viewport_rect().size.x / _size.x
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", int(8.0 * sc))
	l.add_theme_color_override("font_color", Color.BLACK)
	l.add_theme_color_override("font_outline_color", Color.WHITE)
	l.add_theme_constant_override("outline_size", 3)
	l.position = pos_canvas * sc
	add_child(l)


func _labels(names: Array, step: float, x0: float, y0: float) -> void:
	for i in names.size():
		_label(str(names[i]), Vector2(x0 + step * i - 24.0, y0) * _u)


func _page_gestures() -> void:
	var u := _u
	var cols := 6
	for gi in BlackjackPeople.GESTURES.size():
		var g: String = BlackjackPeople.GESTURES[gi]
		var pos := Vector2((gi % cols) * CELL_W * u, (gi / cols) * CELL_H * u)
		_add_layer(pos, Vector2(CELL_W * u, CELL_H * u), func(ci: Control) -> void:
			ci.draw_rect(Rect2(Vector2.ZERO, ci.size), WALL)
			var c := Vector2(roundf(CELL_W * 0.5 * u), roundf(22.0 * u))
			var target := Vector2.ZERO
			match g:
				"point_deck":
					target = c + Vector2(44.0, 44.0) * u
				"point_hand":
					target = c + Vector2(4.0, 84.0) * u
				"invite":
					target = c + Vector2(-6.0, 84.0) * u
				"deal":
					target = c + Vector2(24.0, 70.0) * u
				"sweep":
					target = c + Vector2(-34.0, 76.0) * u
				"pay":
					target = c + Vector2(6.0, 84.0) * u
			var t := fposmod(_now() * 0.5, 1.0)
			var mood := "neutral"
			var face := BlackjackPeople.face_params(mood)
			var gz := c + Vector2(0.0, 8.0 * u)
			if target != Vector2.ZERO:
				gz = target
			BlackjackPeople.draw_person(ci, "dealer", c, u, face, gz, g, t, _beat(), target, "body")
			BlackjackDraw.rect(ci, 0.0, c.y + 52.0 * u, ci.size.x, ci.size.y, BlackjackDraw.BAIZE)
			BlackjackDraw.rect(ci, 0.0, c.y + 52.0 * u, ci.size.x, 2.0 * u, BlackjackDraw.RIM)
			BlackjackPeople.draw_person(ci, "dealer", c, u, face, gz, g, t, _beat(), target, "arms")
			if target != Vector2.ZERO:
				_marker(ci, target)
			ci.draw_rect(Rect2(ci.size.x - 1.0, 0.0, 1.0, ci.size.y), Color.BLACK), true)
	for gi in BlackjackPeople.GESTURES.size():
		_label(BlackjackPeople.GESTURES[gi], Vector2((gi % cols) * CELL_W + 2.0, (gi / cols) * CELL_H) * u)


func _page_gaze() -> void:
	var dirs := [Vector2(0, 0), Vector2(0, -1), Vector2(0, 1), Vector2(-1, 0), Vector2(1, 0), Vector2(-1, -1), Vector2(1, -1), Vector2(-1, 1), Vector2(1, 1)]
	var who := ["dealer", "npc_a", "npc_b"]
	_add_layer(Vector2.ZERO, _size, func(ci: Control) -> void:
		var u := _u
		for r in 3:
			for i in 9:
				var c := Vector2(roundf((36.0 + 71.0 * i) * u), roundf((46.0 + 74.0 * r) * u))
				var d: Vector2 = dirs[i]
				var f := BlackjackPeople.face_params("neutral")
				var gz := c + Vector2(0.0, 8.0 * u) if d == Vector2.ZERO else c + d.normalized() * 36.0 * u
				BlackjackPeople.draw_person(ci, who[r], c, u, f, gz, "rest", 0.0, 2.0)
				if d != Vector2.ZERO:
					_marker(ci, gz))


func _page_hands(pi: int) -> void:
	var p: float = [0.2, 0.55, 0.9][clampi(pi, 0, 2)]
	var gl := ["pockets", "lay_money", "push_bet", "reach_deck", "cover_cards", "drop_cards", "empty_pockets", "gather_money"]
	var u := _u
	var full := _size
	var focus := {
		"pockets": Vector2(full.x * 0.5 - 40.0 * u, 0.0), "lay_money": Vector2(70.0 * u, 0.0), "push_bet": Vector2(full.x * 0.5 - 120.0 * u, 0.0), "reach_deck": Vector2(full.x * 0.5 + 60.0 * u, 0.0),
		"cover_cards": Vector2(full.x * 0.5, 0.0), "drop_cards": Vector2(full.x * 0.5, 0.0), "empty_pockets": Vector2(full.x * 0.5, 0.0), "gather_money": Vector2(full.x * 0.5 - 90.0 * u, 0.0),
	}
	var cw := 160.0 * u
	var ch := 115.0 * u
	for gi in gl.size():
		var g: String = gl[gi]
		var cell := Cell.new()
		cell.position = Vector2((gi % 4) * cw, (gi / 4) * ch)
		cell.size = Vector2(cw, ch)
		_sub.add_child(cell)
		var inner := Layer.new()
		inner.size = full
		var fx: float = (focus[g] as Vector2).x
		inner.position = Vector2(-clampf(fx - cw * 0.5, 0.0, full.x - cw), -ch)
		inner.fn = func(ci: Control) -> void: _hands_scene(ci, g, p)
		cell.add_child(inner)
		_layers.append(inner)
		_label("%s %.2f" % [g, p], Vector2((gi % 4) * cw + 4.0, (gi / 4) * ch + 2.0))


func _hands_scene(ci: Control, g: String, p: float) -> void:
	var u := _u
	var s := _size
	ci.draw_rect(Rect2(Vector2.ZERO, s), WALL)
	BlackjackDraw.draw_table(ci, s, u)
	BlackjackDraw.draw_deck(ci, BlackjackDraw.deck_spot(s), u)
	var sp := BlackjackDraw.pile_origin(s)
	ci.draw_rect(Rect2(sp.x, sp.y - 24.0 * u, 70.0 * u, 24.0 * u), Color("86c79a"))
	ci.draw_rect(Rect2(BlackjackDraw.bet_spot(s) - Vector2(12.0, 5.0) * u, Vector2(24.0, 10.0) * u), Color("86c79a"))
	BlackjackDraw.draw_card(ci, {"rank": 1, "suit": 0}, BlackjackDraw.card_spot("player", 0, s), u, true)
	BlackjackDraw.draw_card(ci, {"rank": 10, "suit": 1}, BlackjackDraw.card_spot("player", 1, s), u, true)
	BlackjackPeople.draw_player_hands(ci, s, u, g, p, {})
