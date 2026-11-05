extends Control
## Preview of the money kit, rendered through a low-res SubViewport shown nearest-neighbour exactly like the game. 640 x 230 by default; RW_GALLERY_LOW=1 gives the 320 x 115 setting.
## RW_GALLERY_PAGE picks the page: 0 = every denomination and the piles, 1 = the transitions (snapshots and one running loop) and the touch-target hint.

const TABLE := Color(0.10, 0.26, 0.19)
const TABLE_DARK := Color(0.09, 0.23, 0.17)

var _size := Vector2i(640, 230)
var _page := 0
var _t := 0.0
var _canvas: Control


class Canvas:
	extends Control
	var draw_fn: Callable

	func _draw() -> void:
		draw_fn.call(self)


func _ready() -> void:
	if OS.get_environment("RW_GALLERY_LOW") == "1":
		_size = Vector2i(320, 115)
	_page = int(OS.get_environment("RW_GALLERY_PAGE")) if not OS.get_environment("RW_GALLERY_PAGE").is_empty() else 0
	var vp := SubViewport.new()
	vp.size = _size
	vp.disable_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	_canvas = Canvas.new()
	_canvas.size = Vector2(_size)
	_canvas.draw_fn = _paint
	vp.add_child(_canvas)
	var tr := TextureRect.new()
	tr.texture = vp.get_texture()
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(tr)


func _process(delta: float) -> void:
	_t += delta
	_canvas.queue_redraw()


func _paint(ci: CanvasItem) -> void:
	var u := _size.y / 230.0
	ci.draw_rect(Rect2(Vector2.ZERO, Vector2(_size)), TABLE)
	for i in 6:
		ci.draw_rect(Rect2(0, roundf(i * 40.0 * u), _size.x, roundf(20.0 * u)), TABLE_DARK)
	if _page == 0:
		_page_items(ci, u)
	else:
		_page_transitions(ci, u)


func _page_items(ci: CanvasItem, u: float) -> void:
	var x := 22.0
	for d in [500, 1000, 2000]:
		var sz := MoneyDraw.item_size(d, u)
		MoneyDraw.draw_note(ci, d, Vector2(x + sz.x * 0.5, 16.0 * u), u)
		x += sz.x + 5.0 * u
	x += 8.0 * u
	for d in [200, 100, 50, 20, 10, 5, 2, 1]:
		var sz := MoneyDraw.item_size(d, u)
		MoneyDraw.draw_coin(ci, d, Vector2(x + sz.x * 0.5, 16.0 * u), u)
		x += sz.x + 5.0 * u
	var amounts := [2000, 1500, 2750, 4000, 350, 50]
	for i in amounts.size():
		var col := i % 3
		var row := i / 3
		var o := Vector2((78.0 + col * 210.0) * u, (66.0 + row * 80.0) * u)
		MoneyDraw.draw_pile(ci, amounts[i], o, u)


func _page_transitions(ci: CanvasItem, u: float) -> void:
	var marks := [0.0, 0.3, 0.6, 1.0]
	for row in 2:
		var from_p := 2000 if row == 0 else 1500
		var to_p := 1500 if row == 0 else 2750
		for i in marks.size():
			var o := Vector2((40.0 + i * 108.0) * u, (30.0 + row * 82.0) * u)
			var away := o + Vector2(52.0, -22.0) * u
			if row == 0 and i == 0:
				pass
			MoneyDraw.draw_transition(ci, from_p, to_p, marks[i], o, u, away)
			ci.draw_rect(Rect2(away - Vector2(1, 1) * u, Vector2(2, 2) * u), Color(1, 0.9, 0.5, 0.5))
	# the running loop
	var o2 := Vector2(490.0 * u, 30.0 * u)
	var loop := fposmod(_t / 4.0, 1.0)
	var p := clampf(loop * 1.4 - 0.1, 0.0, 1.0)
	var fwd := int(_t / 4.0) % 2 == 0
	MoneyDraw.draw_transition(ci, 2000 if fwd else 1500, 1500 if fwd else 2000, p, o2, u, o2 + Vector2(70.0, -10.0) * u)
	# the touch target hint on the top fiver of a £20 pile
	var o3 := Vector2(490.0 * u, 112.0 * u)
	MoneyDraw.draw_pile(ci, 2000, o3, u)
	MoneyDraw.draw_target_hint(ci, MoneyDraw.top_note_rect(2000, o3, u), u, _t * 174.0 / 60.0)
