extends TestCase
## Section tap (work package D): SectionPicker.index_for, LaneInput.area_tapped and the 1/2/3 section keys.

var _taps: Array = []
var _pressed: Array = []
var _keys: Array = []


func _lane() -> LaneInput:
	var lane := LaneInput.new()
	tree.root.add_child(lane)
	lane.rect_provider = func() -> Dictionary: return {1: Rect2(0, 500, 300, 200), 2: Rect2(300, 500, 300, 200)}
	lane.area_provider = func() -> Rect2: return Rect2(0, 0, 1280, 400)
	_taps = []
	_pressed = []
	_keys = []
	lane.area_tapped.connect(func(pos: Vector2) -> void: _taps.append(pos))
	lane.button_pressed.connect(func(button: int, _id: int) -> void: _pressed.append(button))
	lane.section_key.connect(func(index: int) -> void: _keys.append(index))
	return lane


func _touch(pos: Vector2, pressed: bool, index: int = 0) -> InputEventScreenTouch:
	var ev := InputEventScreenTouch.new()
	ev.index = index
	ev.position = pos
	ev.pressed = pressed
	return ev


func test_index_for_picks_the_nearest_point_by_x() -> void:
	var xs := [200.0, 640.0, 1080.0]
	assert_eq(SectionPicker.index_for(0.0, xs), 0)
	assert_eq(SectionPicker.index_for(200.0, xs), 0)
	assert_eq(SectionPicker.index_for(419.0, xs), 0)
	assert_eq(SectionPicker.index_for(421.0, xs), 1)
	assert_eq(SectionPicker.index_for(640.0, xs), 1)
	assert_eq(SectionPicker.index_for(861.0, xs), 2)
	assert_eq(SectionPicker.index_for(5000.0, xs), 2)
	assert_eq(SectionPicker.index_for(-50.0, xs), 0)


func test_index_for_edge_cases() -> void:
	assert_eq(SectionPicker.index_for(100.0, []), -1)
	assert_eq(SectionPicker.index_for(100.0, [500.0]), 0)
	assert_eq(SectionPicker.index_for(420.0, [200.0, 640.0]), 0, "a tie goes to the lower index")


func test_touch_in_the_area_outside_the_pads_emits_area_tapped() -> void:
	var lane := _lane()
	lane._input(_touch(Vector2(200, 250), true))
	assert_eq(_taps.size(), 1)
	assert_eq(_taps[0], Vector2(200, 250))
	assert_eq(_pressed.size(), 0)
	lane._input(_touch(Vector2(200, 250), false))
	assert_eq(_taps.size(), 1, "the release is not a tap")
	lane.queue_free()


func test_touch_on_a_pad_does_not_emit_area_tapped() -> void:
	var lane := _lane()
	lane._input(_touch(Vector2(100, 600), true))
	assert_eq(_taps.size(), 0)
	assert_eq(_pressed, [1])
	lane._input(_touch(Vector2(100, 600), false))
	lane.queue_free()


func test_pad_inside_the_area_wins_over_the_tap() -> void:
	var lane := _lane()
	lane.area_provider = func() -> Rect2: return Rect2(0, 0, 1280, 720)  # the area reaches under the pads
	lane._input(_touch(Vector2(100, 600), true))
	assert_eq(_taps.size(), 0)
	assert_eq(_pressed, [1])
	lane._input(_touch(Vector2(100, 600), false))
	lane.queue_free()


func test_touch_outside_the_area_and_pads_is_ignored() -> void:
	var lane := _lane()
	lane._input(_touch(Vector2(900, 450), true))  # between the area and the pad strip, no pad there
	assert_eq(_taps.size(), 0)
	assert_eq(_pressed.size(), 0)
	lane.queue_free()


func test_no_area_provider_means_no_area_taps() -> void:
	var lane := _lane()
	lane.area_provider = Callable()
	lane._input(_touch(Vector2(200, 250), true))
	assert_eq(_taps.size(), 0)
	lane.queue_free()


func test_disabled_input_gives_no_taps() -> void:
	var lane := _lane()
	lane.enabled = false
	lane._input(_touch(Vector2(200, 250), true))
	assert_eq(_taps.size(), 0)
	lane.queue_free()


func _key(code: int, pressed: bool = true, echo: bool = false) -> InputEventKey:
	var ev := InputEventKey.new()
	ev.keycode = code
	ev.physical_keycode = code
	ev.pressed = pressed
	ev.echo = echo
	return ev


func test_keys_1_2_3_pick_sections() -> void:
	var lane := _lane()
	lane._input(_key(KEY_1))
	lane._input(_key(KEY_2))
	lane._input(_key(KEY_3))
	assert_eq(_keys, [0, 1, 2])
	lane._input(_key(KEY_1, false))
	lane._input(_key(KEY_2, true, true))
	lane._input(_key(KEY_4))
	assert_eq(_keys, [0, 1, 2], "releases, echoes and other digits are ignored")
	lane.queue_free()
